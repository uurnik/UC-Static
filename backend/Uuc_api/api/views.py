from time import sleep
# from scrapli.driver.core import cisco_iosxe
import yaml
import os
# from netaddr import IPNetwork, IPAddress
# from ipaddress import IPv4Interface, ip_network, ip_address, ip_interface
# from ttp import ttp
# import dns.update as dnsupdate
# import dns.query as dnsquery
# import dns.resolver as dnsresolver
from .helpers.pre_checks.pre_config import dns_conn_check

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    permission_classes,

)
from rest_framework import status
from django.http import  JsonResponse

from api.models import Hosts, Defaults, Routes ,StaticTunnelNet
from api.serializers import (
    HostsSerializer,
    DefaultsSerializer,
)
from .helpers.misc import wildcard_conversion, get_challenge_pass
from .helpers.inventory_builder import Myinventory, get_inventory_data, inventory
from .helpers.misc import (
    create_response,
    convert_to_cidr,
    CoppBWCalculator,
    resolve_host,
)
from .helpers.pre_checks.pre_config import PreConfig


from .nornir_stuff.validations.validate_configs import validate
from .nornir_stuff.configure_nodes import (
    send_tcl,
    remove_hosts,
    conf_dmvpn,
    change_on_spoke,
    remove_hub_from_spoke,
    conf_ip_sla,
    get_routes,
    facts,
    fetch_interface_info,
    configure_copp,
    device_harderning,
    change_ipsec_keys,
    configure_logging,
    get_routing_table_cisco,
)

from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks import text, networking
from nornir import InitNornir
from nornir_scrapli.tasks import send_command as scrape_send
from nornir_scrapli.tasks import send_configs as scrape_config


@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def add_Host(request):
    
    if request.method == "POST":
        serializer = HostsSerializer(data=request.data)
        if serializer.is_valid():
            return serializer.save()
        else:
            return Response(serializer.errors ,status=status.HTTP_400_BAD_REQUEST)


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



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def configure(request, option):
    """
    view to configure the network with dmvpn, the 'option'( int-> 1,2 or 3) argument will be passed to the
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
    dns_conn = dns_conn_check(dns)
    if dns_conn == False:
        return JsonResponse({'error':'no connectivity to dns'}, status=status.HTTP_408_REQUEST_TIMEOUT)

    headend_vendor,static_sites=PreConfig().assign_static_tunnels()
    nr = inventory()


    # result_2 = nr.run(task=get_challenge_pass)
    result_1 = nr.run(
        task=conf_dmvpn, nr=nr, dia=DIA, other_services=other_services, dns=dns,
        headend_vendor=headend_vendor,static_sites=static_sites
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




@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def swipe_ipsec_keys(request):
    """
    View For Changing IPsec Keys
    """
    return DefaultsSerializer.change_ipsec_key(request.data)


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