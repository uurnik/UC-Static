from time import sleep
from scrapli.driver.core import cisco_iosxe
import yaml
import os
import asyncio
from netaddr import IPNetwork, IPAddress
from ipaddress import IPv4Interface, ip_network, ip_address, ip_interface
from ttp import ttp
import dns.update as dnsupdate
import dns.query as dnsquery
import dns.resolver as dnsresolver
import socket

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import JSONParser, BaseParser
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    renderer_classes,
)
from rest_framework import status
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError
from .users.utils import IsSuperUser


from api.models import Hosts, Defaults, TunnelPool, CacheTable, Account, Routes ,StaticTunnelNet

from api.serializers import (
    HostsSerializer,
    DefaultsSerializer,
)


from .helpers.get_tunnel_pool_list import add_tunnel_pool
from .helpers.distribute_tunnel_ip import update_defaults_nhs
from .helpers.misc import wildcard_conversion, get_challenge_pass , check_conn
from .helpers.inventory_builder import Myinventory, get_inventory_data, inventory
from .helpers.misc import (
    do_ping,
    test_ssh_conn,
    create_response,
    convert_to_cidr,
    CoppBWCalculator,
    do_poll,
    resolve_host,
)
from .nornir_stuff.validations.validate_configs import validate
from .nornir_stuff.configure_nodes import (
    send_tcl,
    remove_hosts,
    conf_dmvpn,
    fetch_cdp_data,
    change_on_spoke,
    remove_hub_from_spoke,
    conf_ip_sla,
    get_routes,
    facts,
    fetch_interface_info,
    configure_copp,
    device_harderning,
    fortigate_neighbors,
    juniper_neighbors,
    change_ipsec_keys,
    configure_logging,
    get_routing_table_cisco,
)

from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks import text, networking
from nornir.core.deserializer.inventory import Inventory
from nornir import InitNornir
from nornir_scrapli.tasks import send_command as scrape_send
from nornir_scrapli.tasks import send_configs as scrape_config


@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def add_Host(request):
    """
    function to add Hosts in the Hosts table, it will assign the tunnel IP to the host being added,
    first looking for tunnel IP in the CacheTable, if not found,
    An unused IP will assigned from the TunnelPool Table,
    if host being added is a HUB then its NBMA and tunnel IP will also be added to Defaults Table
    """
    if request.method == "POST":
        serializer = HostsSerializer(data=request.data)
        if serializer.is_valid():
            have_ip = False
            # checking if tunnel ip for the host exists in the cache table , if found that ip is assigned as tunnel ip
            # Checked on the bases of the WAN ip of the host
            for cached_ip in CacheTable.objects.all():
                if cached_ip.device_ip == serializer.validated_data["ip"]:
                    serializer.validated_data["tunnel_ip"] = cached_ip.ip
                    cached_ip.save()
                    try:
                        serializer.save()
                    except IntegrityError:
                        return JsonResponse(
                            {"detail": "Host with this IP/name already exists"},
                            status=status.HTTP_403_FORBIDDEN,
                        )

                    update_defaults_nhs(cached_ip.ip, serializer)
                    have_ip = True
                    break
                else:
                    continue
            ##########################################################################################################

            # Assign tunnel IP from TunnelPool if iIP not found in Cache Table, Assigned IP is the marked as used
            if have_ip is False:
                tunnel_ip = TunnelPool.objects.filter(is_used=False)[0]
                serializer.validated_data["tunnel_ip"] = tunnel_ip.ip
                tunnel_ip.is_used = True
                insert_cache = CacheTable(
                    ip=tunnel_ip.ip,
                    in_use=True,
                    device_ip=serializer.validated_data["ip"],
                )
                insert_cache.save()
                tunnel_ip.save()
                try:
                    serializer.save()
                except IntegrityError:
                    return JsonResponse(
                        {"detail": "Host with this IP/name already exists"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                update_defaults_nhs(tunnel_ip.ip, serializer)
                have_ip = True
            else:
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED)
            #######################################################################################################
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Return all the Host data to the user
    if request.method == "GET":
        if request.query_params.get("name"):
            name = request.query_params.get("name")
            device = Hosts.objects.get(name=name)
            serializer = HostsSerializer(device)
            return JsonResponse(serializer.data, safe=False)

        devices = Hosts.objects.all()
        serializer = HostsSerializer(devices, many=True)
        return JsonResponse(serializer.data, safe=False)
    #######################################


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_host(request, pk):
    """
    function to delete a Host from Database, if host is configured, first, it will be removed from the network
    """
    # Check if the Host exists in the data base, if not, return 404.
    try:
        dbHost = Hosts.objects.get(name=pk)
    except Hosts.DoesNotExist:
        return JsonResponse(
            {"detail": "Host does not exist"}, status=status.HTTP_404_NOT_FOUND
        )
    ################################################################

    dbDefaults = Defaults.objects.get(pk=1)
    option = dbDefaults.access_type

    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    if dbHost.group == "SPOKE":
        # if Host being deleted is spoke and it is not configured then simply delete it from DB
        if dbHost.is_configured == False:
            Hosts.objects.get(pk=pk).delete()
            return JsonResponse({"status": f"{pk} deleted"})
        ############################################################################################

        elif dbHost.is_configured == True:
            # if Spoke being deleted is Configured,first remove the configuration then delete from the DB
            spoke_to_remove = nr.filter(F(name=pk))
            result_1 = spoke_to_remove.run(
                task=remove_hosts, nr=nr, Hosts=Hosts, Defaults=Defaults
            )

            if option == 1:
                # if option 1 configured then also remove ACL (used for NAT) statements from HUB
                for n in spoke_to_remove.inventory.hosts.keys():
                    commands = [
                        "ip access-list extended uurnik",
                        f"no permit ip host {spoke_to_remove.inventory.hosts[n].data['loop_back'].split()[0]} any",
                    ]

                spoke_networks = spoke_to_remove.inventory.hosts[n].data["routes"]
                for network in spoke_networks:
                    network = network.split(" ")
                    command_string = f"no permit ip {network[0]} {wildcard_conversion(network[1])} any"
                    commands.append(command_string)

                hubs = nr.filter(F(groups__contains="HUB") & F(is_configured=True))
                change_hub = hubs.run(task=scrape_config, configs=commands)

                #################################################################################
            Hosts.objects.get(pk=pk).delete()

            return JsonResponse({"status": f"{pk} deleted "})
        ######################################################################################

    elif dbHost.group == "HUB":
        # if host being deleted is a HUB and it is not configured then remove its tunnel IP & NBMA address from the Defaults Table
        # then delete the host from DB
        if dbHost.is_configured == False:
            hub_to_remove = nr.filter(F(name=pk))

            fqdn = ""
            for i in hub_to_remove.inventory.hosts.keys():
                hub_tunnel_ip = hub_to_remove.inventory.hosts[i].data["tunnel_ip"]
                nbma_ip = hub_to_remove.inventory.hosts[i].hostname
                try:
                    fqdn = hub_to_remove.inventory.hosts[i].data["fqdn"]
                except:
                    pass

            Hosts.objects.get(name=pk).delete()

            nhs_server_list = dbDefaults.nhs_server.split(",")
            try:
                nhs_server_list.remove(hub_tunnel_ip)
            except:
                pass
            dbDefaults.nhs_server = ",".join(nhs_server_list)

            nhs_nbma_list = dbDefaults.nhs_nbma.split(",")
            nhs_nbma_list.remove(nbma_ip)
            dbDefaults.nhs_nbma = ",".join(nhs_nbma_list)

            # remove the hub's fqdn from Defualts nhs list
            if len(fqdn) != 0:
                try:
                    hubs_fqdn_list = dbDefaults.hubs_fqds.split(",")
                    hubs_fqdn_list.remove(fqdn)
                    dbDefaults.hubs_fqds = ",".join(hubs_fqdn_list)
                except:
                    pass

            dbDefaults.save()

            return JsonResponse({"status": f"{pk} deleted"})
        ###############################################################################################################

        if dbHost.is_configured == True:
            # if HUB is configured then first remove the neighborship from other HUBs and SPOKEs and delete its NBMA & tunnel IP from Defaults
            hub_to_remove = nr.filter(F(name=pk) & F(groups__contains="HUB"))
            result = hub_to_remove.run(
                task=remove_hosts, nr=hub_to_remove, Hosts=Hosts, Defaults=Defaults
            )

            fqdn = ""
            for i in hub_to_remove.inventory.hosts.keys():
                hub_tunnel_ip = hub_to_remove.inventory.hosts[i].data["tunnel_ip"]
                nbma_ip = hub_to_remove.inventory.hosts[i].hostname
                try:
                    fqdn = hub_to_remove.inventory.hosts[i].data["fqdn"]
                except:
                    pass

            other_hubs = nr.filter(~F(name=pk) & F(groups__contains="HUB"))
            _result_other_hubs = other_hubs.run(
                task=scrape_config,
                configs=[
                    "router bgp 65414",
                    f"no neighbor {hub_tunnel_ip} peer-group UURNIK_CONNECT",
                ],
            )

            spokes = nr.filter(F(groups__contains="SPOKE"))
            for n in hub_to_remove.inventory.hosts.keys():
                _spoke_result = spokes.run(
                    task=remove_hub_from_spoke,
                    option=option,
                    hub_tunnel_ip=hub_to_remove.inventory.hosts[n].data["tunnel_ip"],
                    hub_nbma=hub_to_remove.inventory.hosts[n].hostname,
                )

            Hosts.objects.get(name=pk).delete()

            nhs_server_list = dbDefaults.nhs_server.split(",")
            nhs_server_list.remove(hub_tunnel_ip)
            dbDefaults.nhs_server = ",".join(nhs_server_list)

            nhs_nbma_list = dbDefaults.nhs_nbma.split(",")
            nhs_nbma_list.remove(nbma_ip)
            dbDefaults.nhs_nbma = ",".join(nhs_nbma_list)

            if len(fqdn) != 0:
                try:
                    hubs_fqdn_list = dbDefaults.hubs_fqds.split(",")
                    hubs_fqdn_list.remove(fqdn)
                    dbDefaults.hubs_fqds = ",".join(hubs_fqdn_list)
                except:
                    pass

            dbDefaults.save()

            return JsonResponse({"status": f"{pk} deleted"})
        ########################################################################################################################


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facts(request):
    """
    function to gather the facts about devices
    1. Check the device Platform and update Hosts table
    2. Gather hostname,interfaces,model,serial_no,os_version ,vendor
    """
    defaultDB = Defaults.objects.get(pk=1)
    response = []

    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    hubs = nr.filter(F(groups__contains="HUB"))
    primary_hub = list(hubs.inventory.hosts.keys())[0]
    primary_hub_dict = hubs.filter(F(name=primary_hub))
    result_primary = primary_hub_dict.run(task=facts)

    hub_fqdn = result_primary[primary_hub][0].result
    response.append({"name": primary_hub, "failed": result_primary[primary_hub].failed})

    if hub_fqdn not in defaultDB.hubs_fqds:
        defaultDB.hubs_fqds = defaultDB.hubs_fqds + "," + hub_fqdn
        defaultDB.save()

    devices = nr.filter(~F(name=primary_hub))
    result = devices.run(task=facts)

    for host in devices.inventory.hosts.keys():
        response.append(
            {"name": devices.inventory.hosts[host].name, "failed": result[host].failed}
        )

    return JsonResponse(response, safe=False)


############################## Temporary ###############################

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_inventory(request):
    """
    temporary function to get nornir inventory, for debug and testing purpose
    endpoint -> /api/inventory/
    """
    nr = inventory()
    a_inventory = Inventory.serialize(nr.inventory).dict()
    return JsonResponse({"inventory": a_inventory})


###########################################################################


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def configure(request, option):
    """
    function to configure the network with dmvpn, the 'option'( int-> 1,2 or 3) argument will be passed to the
    configuration function to configure the access type of the network as demanded by the user.
    """
    other_services = "n"
    DIA = "n"

    if option == 1:
        DIA = "n"
    elif option == 2:
        DIA = "y"
    elif option == 3:
        other_services = "y"

    dns = request.data["dns"]
    ######################## Check DNS connectivity ######################
    dns_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dns_socket.settimeout(5)
    result_of_check = dns_socket.connect_ex((dns, 53))
    if result_of_check == 0:
        pass
    else:
        return JsonResponse(
            {"error": "No connectivity to DNS"}, status=status.HTTP_408_REQUEST_TIMEOUT
        )

    nr = inventory()
    headend= nr.filter(F(vendor="Cisco") & F(groups__contains="HUB"))
    fortigate= nr.filter(~F(vendor="Cisco"))
    headend_device = list(headend.inventory.hosts.keys())[0]
    headend_vendor = headend.inventory.hosts[headend_device].data['vendor']


    static_sites=[]
    if headend_vendor == "Cisco" and len(list(fortigate.inventory.hosts.keys())) > 0:
        tunnel_id=414   
        for device in fortigate.inventory.hosts.keys():
            dbHost = Hosts.objects.get(name=fortigate.inventory.hosts[device].name)
            static_tunnel = StaticTunnelNet.objects.filter(vendor="fortigate" , used=False)[0]
            dbHost.static_tunnel_network = static_tunnel.network
            static_tunnel.used=True
            static_tunnel.save()
            dbHost.save()

            tunnel_id += 1
            
            remote_tunnel_ip = static_tunnel.network.split(".")[3]
            remote_temp = static_tunnel.network.split(".")[:3]
            remote_temp.append(str(int(remote_tunnel_ip) + 2))
            remote_tunnel_ip = ".".join(remote_temp)



            network_tunnel = static_tunnel.network.split(".")[3]
            temp = static_tunnel.network.split(".")[:3]
            temp.append(str(int(network_tunnel) + 1))
            tunnel_ip = ".".join(temp)


            

            static_sites.append({
                "site_name":fortigate.inventory.hosts[device].name,
                "tunnel_network":static_tunnel.network,
                "site_public_ip":fortigate.inventory.hosts[device].hostname,
                "tunnel_id":tunnel_id,
                "tunnel_ip":tunnel_ip,
                "remote_tunnel_ip":remote_tunnel_ip
            })


    nr = inventory()



    # result_2 = nr.run(task=get_challenge_pass)
    result_1 = nr.run(
        task=conf_dmvpn, nr=nr, dia=DIA, other_services=other_services, dns=dns , headend_vendor=headend_vendor,static_sites=static_sites
    )

    # Save Host's WAN interface, WAN subnet, Next Hop and mark host as configured and update dns server
    data = []
    for i in nr.inventory.hosts.keys():
        db = Hosts.objects.get(ip=nr.inventory.hosts[i].hostname)
        if result_1[i].failed != True:
            db.advertised_interfaces = ",".join(
                nr.inventory.hosts[i].data["advertised_int"]
            )
        spoke_networks_all = result_1[i][0].result

        if result_1[nr.inventory.hosts[i].name].failed == False:
            db.is_configured = True
            try:
                db.snmp_int_index = nr.inventory.hosts[i].data["interface_index"]
            except:
                pass
            db.save()

    dbDefaults = Defaults.objects.get(pk=1)
    dbDefaults.dns = dns
    dbDefaults.access_type = option
    dbDefaults.save()

    # Validate configurations
    validation_result = nr.run(
        task=validate, option=option, spoke_networks_all=spoke_networks_all
    )

    for host in nr.inventory.hosts.keys():
        data.append(
            {
                "name": nr.inventory.hosts[host].name,
                "changed": result_1[host].changed,
                "failed": result_1[host].failed
            }
        )


        dbHost = Hosts.objects.get(name=nr.inventory.hosts[host].name)
        try:
            dbHost.crypto = validation_result[host][0].result["crypto"]
            dbHost.tunnel_int = validation_result[host][0].result["tunnel_int"]
            dbHost.routing = validation_result[host][0].result["routing"]
            dbHost.vrfs = validation_result[host][0].result["vrfs"]
            dbHost.tcl_scp = validation_result[host][0].result["tcl_scp"]
            dbHost.route_map_prefix_list = validation_result[host][0].result[
                "route_map_prefix_list"
            ]
            dbHost.acl = validation_result[host][0].result["acl"]
            dbHost.nat = validation_result[host][0].result["nat"]
        except:
            pass
        dbHost.save()

    #####################################################################################

    return JsonResponse(data, safe=False)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def add_remove_spoke(request, pk):
    """
    function to add/remove a indivisual spoke
    """
    try:
        db = Hosts.objects.get(name=pk)
    except Hosts.DoesNotExist:
        return JsonResponse(
            {"message": "Host does not exist"}, status=status.HTTP_404_NOT_FOUND
        )

    dbDefaults = Defaults.objects.get(pk=1)
    fhrp = dbDefaults.is_sla_configured

    option = dbDefaults.access_type
    other_services = "n"
    DIA = "n"
    if option == 1:
        DIA = "n"
    elif option == 2:
        DIA = "y"
    elif option == 3:
        other_services = "y"

    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    # configure the spoke
    if request.method == "POST":
        if db.is_configured == True:
            return JsonResponse(
                {"message": "Host is Already configured"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            pass

        device = nr.filter(F(groups__contains="SPOKE") & F(name__contains=pk))
        result_1 = device.run(
            task=conf_dmvpn,
            nr=device,
            dia=DIA,
            other_services=other_services,
            dns=nr.inventory.defaults.data["dns"],
        )

        if device.inventory.hosts[pk].platform == "ios":
            # if hsrp configuration exists on the network then add the hsrp configuration on the SPOKE being added
            if fhrp == True:
                track_ip = dbDefaults.track_ip
                for host in device.inventory.hosts.keys():
                    if device.inventory.hosts[host].data["fhrp"] == True:
                        result_2 = device.run(task=conf_ip_sla, track_ip=track_ip)
            ##############################################################################################

            # if network is configured with option 1 then configure the access list on the hub for NAT
            if option == 1:
                for n in device.inventory.hosts.keys():
                    commands = [
                        "ip access-list extended uurnik",
                        f"permit ip host {device.inventory.hosts[n].data['loop_back'].split()[0]} any",
                    ]
                    spoke_networks = device.inventory.hosts[n].data["routes"]
                    custom_routes = device.inventory.hosts[n].data["custom_routes"]
                    for network in spoke_networks:
                        network = network.split(" ")
                        command_string = f"permit ip {network[0]} {wildcard_conversion(network[1])} any"
                        commands.append(command_string)

                    if len(custom_routes) != 0:
                        for network in custom_routes:
                            network = network.split(" ")
                            command_string = f"permit ip {network[0]} {wildcard_conversion(network[1])} any"
                            commands.append(command_string)

                    hubs = nr.filter(F(groups__contains="HUB") & F(is_configured=True))

                    bgp_hub_nei = hubs.run(
                        task=scrape_config,
                        name="configure bgp neighbor on HUB",
                        configs=commands,
                    )
        ##############################################################################################

        # save data to the Database and create return object to return the status whether device is changed/failed or not
        data = {}
        for i in device.inventory.hosts.keys():
            db.advertised_interfaces = ",".join(
                nr.inventory.hosts[i].data["advertised_int"]
            )

            data.update(
                {
                    "name": device.inventory.hosts[i].name,
                    "changed": result_1[i].changed,
                    "failed": result_1[i].failed,
                }
            )

            if result_1[device.inventory.hosts[i].name].failed == False:
                db.is_configured = True

            db.save()

        return JsonResponse(data)
        ###############################################################################################

    # Remove configuration from the SPOKE
    if request.method == "DELETE":

        if db.is_configured == False:
            return JsonResponse(
                {"message": "Host is Not configured"}, status=status.HTTP_403_FORBIDDEN
            )
        else:
            pass

        spoke_to_remove = nr.filter(F(name__contains=pk))
        result_spoke = spoke_to_remove.run(task=remove_hosts)


        hubs_status = []
        if spoke_to_remove.inventory.hosts[pk].platform == "ios":
            # if network is configured with the option 1 then remove the access list (that is used for NAT purposes)
            if option == 1:
                for n in spoke_to_remove.inventory.hosts.keys():
                    commands = [
                        "ip access-list extended uurnik",
                        f"no permit ip host {spoke_to_remove.inventory.hosts[n].data['loop_back'].split()[0]} any",
                    ]

                    spoke_networks = spoke_to_remove.inventory.hosts[n].data["routes"]
                    for network in spoke_networks:
                        network = network.split(" ")
                        command_string = f"no permit ip {network[0]} {wildcard_conversion(network[1])} any"
                        commands.append(command_string)

                    hubs = nr.filter(F(groups__contains="HUB") & F(is_configured=True))
                    change_hub = hubs.run(task=scrape_config, configs=commands)

                # create response object to return the status of change on hub
                for hub in hubs.inventory.hosts.keys():
                    hubs_status.append(
                        {
                            hubs.inventory.hosts[hub].name: {
                                "IP": hubs.inventory.hosts[hub].hostname,
                                "changed": change_hub[hub].changed,
                                "failed": change_hub[hub].failed,
                            }
                        }
                    )
        ###################################################################################################

        # create response object to return the status of Spoke & change the device state in the DB to False
        for spoke in spoke_to_remove.inventory.hosts.keys():
            if (
                result_spoke[spoke_to_remove.inventory.hosts[spoke].name].failed
                == False
            ):
                db.is_configured = False
                db.logging_configured = False
                db.save()

            return_response = create_response(spoke_to_remove, result_spoke)

        if len(hubs_status) != 0:
            data = {"spoke_to_remove": return_response, "hubs": hubs_status}
        else:
            data = {"spoke_to_remove": return_response}

        return JsonResponse(data)
        ##############################################################


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reachability(request):
    """
    function to check the reachability of the hosts
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    return JsonResponse(do_ping(nr), safe=False)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def tear_down(request):
    """
    function to tear down whole network
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    if nr.inventory.defaults.data["access_type"] is not None:
        pass
    else:
        return JsonResponse(
            {"error": "Deploy before configuring device hardening"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Filter the Host that are marked as configured in DB
    configured_hosts = nr.filter(F(is_configured=True))
    # Remove config from Hosts
    result = configured_hosts.run(task=remove_hosts)

    data = []
    for i in configured_hosts.inventory.hosts.keys():
        # Change the is_configured state of the Hosts in the Database to False
        if result[i].failed == False:
            dbHost = Hosts.objects.get(name=configured_hosts.inventory.hosts[i].name)
            dbHost.is_configured = False
            dbHost.logging_configured = False
            dbHost.save()

        data.append(
            {
                "name": configured_hosts.inventory.hosts[i].name,
                "changed": result[configured_hosts.inventory.hosts[i].name].changed,
                "failed": result[configured_hosts.inventory.hosts[i].name].failed,
            }
        )


    # Change the is_sla_configured in Database to False
    dbDefaults = Defaults.objects.get(pk=1)
    dbDefaults.is_sla_configured = False
    dbDefaults.access_type = None
    dbDefaults.is_copp_configured = False
    dbDefaults.save()

    return JsonResponse(data, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cdp_info(request):
    """
    Function to get CDP information from all the Hosts in the Database
    Data is then structured to feed the Viz-js library to create Network Topology on front-end
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################
    # result = nr.run(task=juniper_neighbors)
    # print_result(result)
    # for fortigate devices
    # result = nr.run(task=fortigate_neighbors)
    # devices=[]
    # for host in nr.inventory.hosts.keys():
    #     nr.inventory.hosts[host].name
    #     if result[host].failed == False:
    #         devices.append({"name":nr.inventory.hosts[host].name,"neighbors":result[host][0].result})

    # nodes=[]
    # for k,v in enumerate(devices, 1):
    #     ip = nr.inventory.hosts[v['name']].hostname
    #     site_name = nr.inventory.hosts[v['name']].name
    #     # tunnel_ip = nr.inventory.hosts[hosts[v]].data['tunnel_ip']

    #     if nr.inventory.hosts[v["name"]].groups[0] == 'HUB':
    #         group= 'HUB'
    #     elif nr.inventory.hosts[v["name"]].groups[0] == 'SPOKE':
    #         group='SPOKE'

    #     nodes.append({"id": k , "label": v['name'] ,'shape':'circle',
    #                     'smooth': {'type': 'curvedCW','roundness': 0}, 'font':{ 'color':'white' },
    #                     'group': group ,"title": f"<p><b> Site Name:  {site_name} </b> <br>IP:{ip}</p>"})

    # edges=[]
    # for node in nodes:
    #     if node['group'] =='HUB':
    #         neighbors = result[node['label']][0].result
    #         for neighbor in neighbors:
    #             spoke = nr.filter(F(hostname__contains=neighbor))
    #             neighbor_name=list(spoke.inventory.hosts.keys())[0]
    #             for spoke_node in nodes:
    #                 if spoke_node['label'] == neighbor_name:
    #                     edges.append({'from':node['id'],'to':spoke_node['id']})

    # return JsonResponse({'result':{'nodes':nodes , "edges":edges}})

    # Get CDP data from Hosts
    result = nr.run(task=fetch_cdp_data)
    cdp_dict = {}
    hosts = {}
    for host in nr.inventory.hosts.keys():
        hosts.update({nr.inventory.hosts[host].data["dev_name"]: host})
        if result[host].failed == True:
              cdp_dict[nr.inventory.hosts[host].data["dev_name"]] = {
                "wan_ip": nr.inventory.hosts[host].hostname,
                "tunnel_ip": nr.inventory.hosts[host].data["tunnel_ip"],
                "cdp": [],
            }
        else:
            cdp_dict[nr.inventory.hosts[host].data["dev_name"]] = {
                "wan_ip": nr.inventory.hosts[host].hostname,
                "tunnel_ip": nr.inventory.hosts[host].data["tunnel_ip"],
                "cdp": result[host][1].scrapli_response.textfsm_parse_output(),
            }

    nodes = []
    edges = []

    devices = [k for k in cdp_dict]

    sum_of_devices = 0
    for k, v in enumerate(devices, 1):
        sum_of_devices += 1

    # Create Nodes List
    for k, v in enumerate(devices, 1):
        ip = nr.inventory.hosts[hosts[v]].hostname
        site_name = nr.inventory.hosts[hosts[v]].name

        vendor = nr.inventory.hosts[hosts[v]].data['vendor']

        if nr.inventory.hosts[hosts[v]].groups[0] == "HUB":
            group = "HUB"
        elif nr.inventory.hosts[hosts[v]].groups[0] == "SPOKE":
            group = "SPOKE"


        nodes.append(
            {
                "id": k,
                "name":nr.inventory.hosts[hosts[v]].name,
                "label": v,
                "shape": "image",
                "image": f"{vendor.lower()}.png",
                "group": group,
                "title": f"<p><b> Site Name:  {site_name} </b> <br>IP:{ip}</p>",
            }
        )

        for neighbor in cdp_dict[v]["cdp"]:
            other = 0
            neighbor["neighbor"] = neighbor["neighbor"].split(".")[0]
            if neighbor["local_interface"] != "Tunnel414":
                for node in nodes:
                    if neighbor["neighbor"] == node["label"].split(".")[0]:
                        other += 1

                if other == 0:
                    sum_of_devices += 1
                    if "S" in neighbor["capability"]:
                        pass
                        # nodes.append(
                        #     {
                        #         "id": sum_of_devices,
                        #         "image": "switch-50.png",
                        #         "label": neighbor["neighbor"],
                        #         "shape": "image",
                        #     }
                        # )
                    else:
                        pass
                        # nodes.append(
                        #     {
                        #         "id": sum_of_devices,
                        #         "label": neighbor["neighbor"],
                        #         "shape": "circle",
                        #         "color": "grey",
                        #     }
                        # )

    # only Get Tunnel414 neighbors
    add_uurnik_node = 0
    for k in cdp_dict:
        if len(cdp_dict[k]["cdp"]) == 0:
            edges.append(
                    {
                        "device": k,
                        "neighbor": '',
                        "type": "overlay",
                    }
                )
        for neighbor in cdp_dict[k]["cdp"]:
            if neighbor["local_interface"] == "Tunnel414":
                # add_uurnik_node += 1
                edges.append(
                    {
                        "device": k,
                        "neighbor": neighbor["neighbor"].split(".")[0],
                        "type": "overlay",
                    }
                )
            else:
                edges.append(
                    {
                        "device": k,
                        "neighbor": neighbor["neighbor"].split(".")[0],
                        "type": "underlay",
                    }
                )
    for edge in edges:
        device = edge['device']
        if len([n for n in edges if n['device'] == device and n['type'] == "overlay" ]) == 0 :
            
            edges.append(
                    {
                        "device": device,
                        "neighbor": '',
                        "type": "overlay",
                    }
                )


    if Defaults.objects.get(pk=1).access_type != None:
        sum_of_devices += 1
        nodes.append(
            {
                "id": sum_of_devices,
                "label": "",
                "size": 40,
                "shape": "circularImage",
                "image": "UKS_ICON_COLOR1-01.jpg",
                "color": {
                    "border": "white",
                    "hover": {"border": "white", "background": "white"},
                },
            }
        )

    new_edge = {}
    final_edges = []
    for edge in edges:
        if (
            nr.inventory.hosts[hosts[edge["device"]]].groups[0] == "HUB"
            or nr.inventory.hosts[hosts[edge["device"]]].groups[0] == "SPOKE"
        ):
           
            for node in nodes:
                if edge["device"] == node["label"]:
                    new_edge["from"] = node["id"]
                    if edge["neighbor"] == '':
                    # if edge['type'] == "overlay":
                        final_edges.append({"from": new_edge["from"], "to": sum_of_devices ,"color":"red","width":1.7})
                        continue
                    for node in nodes:
                        if edge["neighbor"] == node["label"].split(".")[0]:
                            new_edge["to"] = node["id"]

            if edge["type"] == "overlay":
                if edge["neighbor"] == '':
                    # final_edges.append({"from": new_edge["from"], "to": sum_of_devices ,"color":"red","width":1.7})
                    pass
                final_edges.append({"from": new_edge["from"], "to": sum_of_devices})
            elif edge["type"] == "underlay":
                pass
                # final_edges.append(
                #     {
                #         "from": new_edge["from"],
                #         "to": new_edge["to"],
                #         "dashes": True,
                #     }
                # )

    data = {"nodes": nodes, "edges": final_edges}

    return JsonResponse({"result": data})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def add_remove_hub(request, pk):
    """
    function to Add or Remove the Hub (other than Primary Hub) individually.
    Along removing or adding configuration to new Hub , change in converged across other Hubs and spokes
    i.e Add/remove nhrp static mapping & BGP neighborship commands
    """
    try:
        db = Hosts.objects.get(name=pk)
    except Hosts.DoesNotExist:
        return JsonResponse(
            {"detail": "Host does not exits"}, status=status.HTTP_404_NOT_FOUND
        )

    # Check if user is using IP SLA service and which access type is being is used
    dbDefaults = Defaults.objects.get(pk=1)
    fhrp = dbDefaults.is_sla_configured
    option = dbDefaults.access_type

    other_services = "n"
    DIA = "n"

    if option == 1:
        DIA = "n"
    elif option == 2:
        DIA = "y"
    elif option == 3:
        other_services = "y"

    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    # if user want to add Hub to network
    if request.method == "POST":

        if db.is_configured == True:
            return JsonResponse(
                {"message": "Host is Already configured"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            pass

        hub_to_add_status = {}
        other_hubs_status = []
        spokes_status = []

        hub_to_add = nr.filter(F(name=pk) & F(groups__contains="HUB"))

        for n in hub_to_add.inventory.hosts.keys():
            hub_tunnel_ip = nr.inventory.hosts[n].data["tunnel_ip"]
            hub_fqdn = hub_to_add.inventory.hosts[n].data["fqdn"]

        # Add BGP neighbor configuration on other hubs
        other_hubs = nr.filter(
            ~F(name=pk) & F(groups__contains="HUB") & F(is_configured=True)
        )
        result_other_hubs = other_hubs.run(
            task=scrape_config,
            configs=[
                "router bgp 65414",
                f"neighbor {hub_tunnel_ip} peer-group UURNIK_CONNECT",
                "address-family ipv4",
                f"neighbor {hub_tunnel_ip} activate ",
            ],
        )
        sleep(2)
        for n in other_hubs.inventory.hosts.keys():
            other_hubs_status.append(
                {
                    other_hubs.inventory.hosts[n].name: {
                        "IP": other_hubs.inventory.hosts[n].hostname,
                        "changed": result_other_hubs[n].changed,
                        "failed": result_other_hubs[n].failed,
                    }
                }
            )

        # configure the HUB
        result = hub_to_add.run(
            task=conf_dmvpn, nr=hub_to_add, dia=DIA, other_services=other_services
        )
        # if hsrp configuration exists on the network then add the hsrp configuration on the SPOKE being added
        if fhrp == True:
            track_ip = dbDefaults.track_ip
            for host in hub_to_add.inventory.hosts.keys():
                if hub_to_add.inventory.hosts[host].data["fhrp"] == True:
                    result_2 = hub_to_add.run(task=conf_ip_sla, track_ip=track_ip)
        ##############################################################################################

        for n in hub_to_add.inventory.hosts.keys():
            hub_to_add_status[hub_to_add.inventory.hosts[n].name] = {
                "IP": hub_to_add.inventory.hosts[n].hostname,
                "changed": result[n].changed,
                "failed": result[n].failed,
            }

            # Save WAN interface name, WAN subnet & Next Hop of the Hub to the DB
            db.advertised_interfaces = ",".join(
                nr.inventory.hosts[n].data["advertised_int"]
            )
            db.save()

            # Change the state of the Host to Configured = True
            if result[n].failed == False:
                dbHost = Hosts.objects.get(name=pk)
                dbHost.is_configured = True

            dbHost.save()

        # Add NHRP static mappings & BGP neighbor on all Configured Spokes
        spokes = nr.filter(F(groups__contains="SPOKE") & F(is_configured=True))
        spoke_result = spokes.run(
            task=change_on_spoke,
            option=option,
            hub_tunnel_ip=hub_tunnel_ip,
            hub_nbma=hub_fqdn,
        )

        for spoke in spokes.inventory.hosts.keys():
            spokes_status.append(
                {
                    spokes.inventory.hosts[spoke].name: {
                        "IP": spokes.inventory.hosts[spoke].hostname,
                        "changed": spoke_result[spoke].changed,
                        "failed": spoke_result[spoke].failed,
                    }
                }
            )

        # Aggregate all the response objects from other HUBs ,Spokes & the HUB being added
        data = {
            "hub_to_add": hub_to_add_status,
            "other_hubs": other_hubs_status,
            "spokes": spokes_status,
        }

        return JsonResponse(data)

    # if user wants the remove the HUB from network
    if request.method == "DELETE":

        if db.is_configured == False:
            return JsonResponse(
                {"message": "Host is not configured"}, status=status.HTTP_403_FORBIDDEN
            )
        else:
            pass
        hubs = nr.filter(F(groups__contains="HUB"))
        primary_hub = list(hubs.inventory.hosts.keys())[0]

        if pk == primary_hub:
            return JsonResponse(
                {"message": "primary central site cannot be removed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        hub_to_remove_status = {}
        other_hubs_status = []
        spokes_status = []

        hub_to_remove = nr.filter(F(name=pk) & F(groups__contains="HUB"))
        for n in hub_to_remove.inventory.hosts.keys():
            hub_tunnel_ip = hub_to_remove.inventory.hosts[n].data["tunnel_ip"]

        # Remove the configuration from the HUB
        result = hub_to_remove.run(task=remove_hosts)
        for n in hub_to_remove.inventory.hosts.keys():
            hub_to_remove_status[hub_to_remove.inventory.hosts[n].name] = {
                "IP": hub_to_remove.inventory.hosts[n].hostname,
                "changed": result[n].changed,
                "failed": result[n].failed,
            }
            # Change the state of the Host to Configured = False
            if result[n].failed == False:
                dbHost = Hosts.objects.get(name=pk)
                dbHost.is_configured = False
                dbHost.logging_configured = False
                dbHost.is_copp_configured = False
                dbHost.save()

        # Remove BGP neighbor configuration from other hubs
        other_hubs = nr.filter(
            ~F(name=pk) & F(groups__contains="HUB") & F(is_configured=True)
        )
        result_other_hubs = other_hubs.run(
            task=scrape_config,
            configs=[
                "router bgp 65414",
                f"no neighbor {hub_tunnel_ip} peer-group UURNIK_CONNECT",
            ],
        )

        for n in other_hubs.inventory.hosts.keys():
            other_hubs_status.append(
                {
                    other_hubs.inventory.hosts[n].name: {
                        "IP": other_hubs.inventory.hosts[n].hostname,
                        "changed": result_other_hubs[n].changed,
                        "failed": result_other_hubs[n].failed,
                    }
                }
            )

        # Remove NHRP static mappings & BGP neighbor on all Configured Spokes
        spokes = nr.filter(F(groups__contains="SPOKE") & F(is_configured=True))
        for n in hub_to_remove.inventory.hosts.keys():
            spoke_result = spokes.run(
                task=remove_hub_from_spoke,
                option=option,
                hub_tunnel_ip=hub_to_remove.inventory.hosts[n].data["tunnel_ip"],
                hub_nbma=hub_to_remove.inventory.hosts[n].hostname,
            )

        for spoke in spokes.inventory.hosts.keys():
            spokes_status.append(
                {
                    spokes.inventory.hosts[spoke].name: {
                        "IP": spokes.inventory.hosts[spoke].hostname,
                        "changed": spoke_result[spoke].changed,
                        "failed": spoke_result[spoke].failed,
                    }
                }
            )

        # Aggregate all the response objects from other HUBs ,Spokes & the HUB being added
        data = {
            "hub_to_remove": hub_to_remove_status,
            "other_hubs": other_hubs_status,
            "spokes": spokes_status,
        }


        return JsonResponse(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_alive(request):
    """
    function to test the ssh connectivity of the hosts
    """
    nr = inventory()

    dns = Defaults.objects.get(pk=1).dns

    if request.query_params.get("name"):
        name = request.query_params.get("name")
        device = nr.filter(F(name=name))
        device.run(task=resolve_host, dns=dns)
        result = device.run(task=test_ssh_conn)
        data = {"name": name, "alive": result[name][0].result}
    else:
        # query dns and update inventory
        if dns != None:
            nr.run(task=resolve_host, dns=dns)
        #####################################
        result = nr.run(task=test_ssh_conn)
        data = []
        for h in nr.inventory.hosts.keys():
            data.append(
                {"name": nr.inventory.hosts[h].name, "alive": result[h][0].result}
            )

    return JsonResponse(data, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ip_sla_conf(request):
    """
    function to configure ip sla and track in HSRP
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    devices = nr.filter(F(fhrp=True))
    result = devices.run(task=conf_ip_sla, track_ip=request.data["track_ip"])

    dbDefaults = Defaults.objects.get(pk=1)
    dbDefaults.track_ip = request.data["track_ip"]
    dbDefaults.is_sla_configured = True
    dbDefaults.save()

    data = []
    for device in devices.inventory.hosts.keys():
        data.append(
            {
                "name": devices.inventory.hosts[device].name,
                "changed": result[device].changed,
                "failed": result[device].failed,
            }
        )


    return JsonResponse(data, safe=False)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def gather_routes(request):
    """
    View for suggesting routes to user
        - return list of directly connected & static routes ( GET)
        - for fortigate only returns directly connected ( GET )
        - POST routes back to the Database ( POST )
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    if request.method == "GET":
        devices = nr.filter(F(is_configured=False))
        result_1 = devices.run(task=get_routes)

        cisco_devices = devices.filter(F(vendor="Cisco"))
        result_2 = cisco_devices.run(task=get_routing_table_cisco)


        all_routes = []
        for host in devices.inventory.hosts.keys():
            if result_1[host].failed == False:
                routes = result_1[host][0].result
                try:
                    Routes.objects.filter(route=host).delete()
                except:
                    pass

                dbHost = Hosts.objects.get(name=host)
                
                if devices.inventory.hosts[host].data['vendor'] == "Cisco":
                    for route in routes:
                        for route_in_table in result_2[host][0].result:
                            in_table = (
                                route_in_table["network"] + "/" + route_in_table["mask"]
                            )
                            if in_table == route:
                                dbRoute = Routes(
                                    route=dbHost,
                                    lan_routes=route,
                                    protocol=route_in_table["protocol"],
                                    advertised=False,
                                )
                                dbRoute.save()
                else:
                    for route in routes:
                        dbRoute = Routes(
                                    route=dbHost,
                                    lan_routes=route,
                                    protocol="S",
                                    advertised=False,
                                )
                        dbRoute.save()

                all_routes.append(
                    {"name": devices.inventory.hosts[host].name, "routes": routes}
                )

        return JsonResponse(all_routes, safe=False)

    if request.method == "POST":
        for data in request.data:
            dbHost = Hosts.objects.get(name=data["name"])


            for route_in_db in Routes.objects.filter(route=dbHost):
                for route in data["routes"]:
                    if route == route_in_db.lan_routes:
                        route_in_db.advertised = True
                        route_in_db.save()

            if data.get("custom") != None:
                for custom_route in data["custom"]:
                    if len(custom_route) != 0:
                        dbRoute = Routes(
                            route=dbHost,
                            custom_route=custom_route,
                            advertised=True,
                            protocol="S",
                        )
                        dbRoute.save()

        return JsonResponse(request.data, safe=False)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_deployed_access_type(request):
    """
    View for getting deployed access type
    """
    dbDefaults = Defaults.objects.get(pk=1)
    access_type_number = dbDefaults.access_type
    device_hardening = dbDefaults.is_device_hardening_configured
    copp_configured = dbDefaults.is_copp_configured

    if access_type_number == 1:
        access_type = "Private WAN only"
    elif access_type_number == 2:
        access_type = "Private WAN + Direct Internet Access"
    elif access_type_number == 3:
        access_type = "Private WAN + Direct Internet Access + Addons"
    else:
        access_type = None
    


    return JsonResponse({"access_type": access_type,"copp":copp_configured,"device_hardening":device_hardening})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_interfaces(request, name):
    """
    View for getting interface information
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    data = []
    device = nr.filter(F(name=name))
    if len(list(device.inventory.hosts.keys())) != 0:
        result = device.run(task=fetch_interface_info)
        host = list(device.inventory.hosts.keys())[0]
        data = result[host][0].result

    return JsonResponse(data, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def copp(request):
    """
    View for configuring Control Plane Policing on Cisco devices
        - check max throughput from model_spec file
        - calculte COPP bandwidth classes and feed to configuration template
    """
    nr = inventory()

    nr = nr.filter(F(vendor="Cisco"))

    if nr.inventory.defaults.data["access_type"] is not None:
        pass
    else:
        return JsonResponse(
            {"error": "Deploy before configuring COPP"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    dbDefaults = Defaults.objects.get(pk=1)
    dns = dbDefaults.dns
    if dns != None:
        result_1 = nr.run(task=resolve_host, dns=dns)
        for h in nr.inventory.hosts.keys():
            if result_1[h].failed == False:
                dbHost = Hosts.objects.get(name=nr.inventory.hosts[h].name)
                dbHost.ip = nr.inventory.hosts[h].hostname
                dbHost.save()

    with open(f"{os.getcwd()}/Uuc_api/api/model_spec_cisco.yaml") as file:
        model_specs = yaml.safe_load(file)

    for host in nr.inventory.hosts.keys():
        model = nr.inventory.hosts[host].data["model"]
        # bw = model_specs[f"Cisco {model}"]
        ## cut 25% for models < 1gig
      
        dbHost = Hosts.objects.get(pk=nr.inventory.hosts[host].name)
        dbHost.copp_bw = 500                # TODO fix this
        dbHost.save()


    nr = inventory()
    nr = nr.filter(F(vendor="Cisco"))


    results = nr.run(task=configure_copp)
    dbDefaults.is_copp_configured = True
    dbDefaults.save()

    response = []
    for host in nr.inventory.hosts.keys():
        response.append(
            {
                "name": nr.inventory.hosts[host].name,
                "changed": results[host].changed,
                "failed": results[host].failed,
            }
        )

    return JsonResponse(response, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def device_hardening(request):
    """
    View for pushing Hardening Commands to devices
    """
    nr = inventory()

    if nr.inventory.defaults.data["access_type"] is not None:
        pass
    else:
        return JsonResponse(
            {"error": "Deploy before configuring device hardening"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################
    cisco_only = nr.filter(F(vendor="Cisco"))

    results = cisco_only.run(task=device_harderning)
    dbDefaults = Defaults.objects.get(pk=1)
    dbDefaults.is_device_hardening_configured = True
    dbDefaults.save()

    data = []
    for host in cisco_only.inventory.hosts.keys():
        data.append(
            {
                "name": cisco_only.inventory.hosts[host].name,
                "changed": results[host].changed,
                "failed": results[host].failed,
            }
        )

    return JsonResponse(data, safe=False)


####################### Incomplete ###################
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def snmp_poll(request):
    """
    View for SNMP polling
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    hosts = []
    community_str = "public"
    avg=None
    if request.query_params.get("avg"):
        avg = True

    if request.query_params.get("name"):
        name = request.query_params.get("name")
        device = nr.filter(F(name=name))
        for host in device.inventory.hosts.keys():
            try:
                hosts.append(
                {
                    "name": nr.inventory.hosts[host].name,
                    "IP": nr.inventory.hosts[host].hostname,
                    "int_index": nr.inventory.hosts[host].data["interface_index"],
                    "wan_int": nr.inventory.hosts[host].data["wan_int"],
                }
            )
            except:
                pass
    else:
        for host in nr.inventory.hosts.keys():
            try:
                hosts.append(
                    {
                        "name": nr.inventory.hosts[host].name,
                        "IP": nr.inventory.hosts[host].hostname,
                        "int_index": nr.inventory.hosts[host].data["interface_index"],
                        "wan_int": nr.inventory.hosts[host].data["wan_int"],

                    }
                )
            except:
                pass

    output = asyncio.run(do_poll(hosts, community_str ,avg=avg))

    return JsonResponse(output, safe=False)


###########################################################################################


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def swipe_ipsec_keys(request):
    """
    View For Changing IPsec Keys
    """
    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    new_key = request.data["new_key"]
    # check if old key matches the key in Db
    if nr.inventory.defaults.data["ipsec_key"] != request.data["old_key"]:
        return JsonResponse(
            {"error": "Invalid Key"}, status=status.HTTP_406_NOT_ACCEPTABLE
        )
    # Key must be of 8-16 characters
    if len(new_key) < 8 or len(new_key) > 16:
        return JsonResponse(
            {"error": "Key must be of 8-16 characters"},
            status=status.HTTP_406_NOT_ACCEPTABLE,
        )
    # check if key contains a digit,a special character and one capital letter
    if (
        any(x.isupper() for x in new_key)
        and any(x.islower() for x in new_key)
        and any(x.isdigit() for x in new_key)
        and any(x.isalnum() for x in new_key)
    ):
        import string

        invalidChars = set(string.punctuation.replace("_", ""))
        if any(char in invalidChars for char in new_key):
            pass
        else:
            return JsonResponse(
                {
                    "error": "Must include 1 upper case letter,a digit and a special character"
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
    else:
        return JsonResponse(
            {
                "error": "Must include 1 upper case letter,a digit and a special character"
            },
            status=status.HTTP_406_NOT_ACCEPTABLE,
        )

    result = nr.run(task=change_ipsec_keys, new_key=new_key)

    # Save new key in DB
    dbDefaults = Defaults.objects.get(pk=1)
    dbDefaults.ipsec_key = request.data["new_key"]
    dbDefaults.save()

    data = []
    for host in nr.inventory.hosts.keys():
        data.append(
            {
                "name": nr.inventory.hosts[host].name,
                "changed": result[host].changed,
                "failed": result[host].failed,
            }
        )

    return JsonResponse(data, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_logging(request, pk):

    nr = inventory()

    # query dns and update inventory
    dns = Defaults.objects.get(pk=1).dns
    if dns != None:
        nr.run(task=resolve_host, dns=dns)
    #####################################

    logging_host = request.data["logging_host"]
    logging_level = request.data["logging_level"]
    facility = request.data["facility"]

    device = nr.filter(F(name=pk))

    result = device.run(
        task=configure_logging,
        logging_host=logging_host,
        logging_level=logging_level,
        facility=facility,
    )

    if result[pk].failed == False:
        dbHost = Hosts.objects.get(pk=pk)
        dbHost.logging_host = logging_host
        dbHost.logging_level = logging_level
        dbHost.logging_facility = facility
        dbHost.logging_configured = True
        dbHost.save()

    response = {
        "name": device.inventory.hosts[pk].name,
        "failed": result[pk].failed,
        "changed": result[pk].changed,
    }

    return JsonResponse(response)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    """
    function to test the ssh connectivity of the hosts
    """
    nr = inventory()
    data = {}

    managed_inv = nr.filter(F(is_configured=True))
    data['managed'] = len(managed_inv.inventory.hosts.keys())

    unmanaged = nr.filter(F(is_configured=False))
    data['unmanaged'] = len(unmanaged.inventory.hosts.keys())

    data['total'] = len(nr.inventory.hosts.keys())

    return JsonResponse(data)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ping_test(request):
    """
    function to test the ssh connectivity of the hosts
    """
    data={}
    dev_name = request.query_params.get("name")
    dest = request.query_params.get("dest")
    nr = inventory()
    device = nr.filter(F(dev_name=dev_name))

    result = device.run(task=check_conn , dest=dest)

    for host in device.inventory.hosts.keys():
        data['result'] = result[host][0].result


    return JsonResponse(data)