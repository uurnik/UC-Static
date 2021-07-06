from api.models import Defaults, Hosts, Routes

from nornir.core.deserializer.inventory import Inventory
from nornir import InitNornir
from netaddr import IPNetwork
import os
from django.conf import settings


def get_inventory_data(Defaults, Hosts):
    """function to create the nornir inventory structure from DB objects

    :params:
        Defaults: Defaults DB table
        Hosts: Hosts DB table
    """
    all_defaults = {}
    defaults_val = Defaults.objects.get(pk=1)

    nhs_s = []
    for val in defaults_val.nhs_server.split(","):
        if val != "none":
            nhs_s.append(val)

    nhs_n = []
    for val in defaults_val.nhs_nbma.split(","):
        if val != "none":
            nhs_n.append(val)

    hubs_fqdn = []
    for fqdn in defaults_val.hubs_fqds.split(","):
        if len(fqdn) != 0:
            hubs_fqdn.append(fqdn)

            # "cmd_verify":False,"blocking_timeout":100
    all_defaults = {
        "connection_options": {
            "netmiko": {"extras": {"global_delay_factor": 1}},
            "scrapli": {
                "extras": {
                    "transport": "ssh2",
                    "auth_strict_key": False,
                    "timeout_transport": 45,
                    "timeout_ops": 45,
                    "timeout_socket": 10,
                }
            },
        },
        "data": {
            "tunnel_int": defaults_val.tunnel_int,
            "dns": defaults_val.dns,
            "policy_num": defaults_val.policy_num,
            "ipsec_key": defaults_val.ipsec_key,
            "trans_set": defaults_val.trans_name,
            "profile_name": defaults_val.profile_name,
            "nhs_server": nhs_s,
            "nhs_nbma": nhs_n,
            "hubs_fqdn": hubs_fqdn,
            "access_type": defaults_val.access_type,
            "ip_sla_process": defaults_val.ip_sla_process,
            "track_ip": defaults_val.track_ip,
            "is_sla_configured": defaults_val.is_sla_configured,
            "is_device_hardening_configured": defaults_val.is_device_hardening_configured,
            "is_copp_configured": defaults_val.is_copp_configured,
        },
    }

    all_hosts = {}
    for n in Hosts.objects.all():
        routes = []
        custom_route = []
        for route in Routes.objects.filter(route=n):
            if len(route.lan_routes) != 0:
                if route.advertised == True:
                    prefix = route.lan_routes.split("/")[0]
                    mask = IPNetwork(route.lan_routes).netmask
                    address = str(prefix) + " " + str(mask)
                    routes.append(address)

            if len(route.custom_route) != 0:
                prefix = route.custom_route.split(" ")[0].split("/")[0]
                mask = IPNetwork(route.custom_route.split(" ")[0]).netmask
                address = (
                    str(prefix)
                    + " "
                    + str(mask)
                    + " "
                    + str(route.custom_route.split(" ")[1])
                )
                custom_route.append(address)

        if n.platform == "generic":

            all_hosts[n.name] = {
                "username": n.username,
                "password": n.password,
                "hostname": n.ip,
                "connection_options": {
                    "scrapli": {
                        "platform": "generic",
                        "extras": {
                            "comms_prompt_pattern": r"^.*?\s?#\s",
                            "transport": "ssh2",
                            "auth_strict_key": False,
                            "timeout_transport": 10,
                            "timeout_ops": 15,
                            "timeout_socket": 10,
                        },
                    }
                },
                "groups": [n.group],
                "platform": n.platform,
                "data": {
                    "loop_back": n.loop_back,
                    "tunnel_ip": n.tunnel_ip,
                    "wan_int": n.wan_int,
                    "is_configured": n.is_configured,
                    "model": n.model,
                    "os_version": n.os_version,
                    "interfaces": n.interfaces,
                    "serial_no": n.serial_no,
                    "dev_name": n.dev_name,
                    "fqdn": n.fqdn,
                    "wan_subnet": n.wan_subnet,
                    "next_hop": n.next_hop,
                    "fhrp": n.fhrp,
                    "fhrp_interface": n.fhrp_interface,
                    "ram_size": n.ram_size,
                    "primary_router": n.primary_router,
                    "virtual_ip": n.virtual_ip,
                    "routes": routes,
                    "custom_routes": custom_route,
                    "advertised_interfaces": n.advertised_interfaces.split(","),
                    "validations": {
                        "crypto_validation": n.crypto,
                        "tunnel_int_validation": n.tunnel_int,
                        "routing_validation": n.routing,
                    },
                },
            }
        else:
            all_hosts[n.name] = {
                "username": n.username,
                "password": n.password,
                "hostname": n.ip,
                "groups": [n.group],
                "platform": n.platform,
                "data": {
                    "loop_back": n.loop_back,
                    "tunnel_ip": n.tunnel_ip,
                    "wan_int": n.wan_int,
                    "is_configured": n.is_configured,
                    "model": n.model,
                    "os_version": n.os_version,
                    "interfaces": n.interfaces,
                    "serial_no": n.serial_no,
                    "dev_name": n.dev_name,
                    "fqdn": n.fqdn,
                    "wan_subnet": n.wan_subnet,
                    "next_hop": n.next_hop,
                    "fhrp": n.fhrp,
                    "fhrp_interface": n.fhrp_interface,
                    "ram_size": n.ram_size,
                    "primary_router": n.primary_router,
                    "virtual_ip": n.virtual_ip,
                    "routes": routes,
                    "custom_routes": custom_route,
                    "advertised_interfaces": n.advertised_interfaces.split(","),
                    "interface_index": n.snmp_int_index,
                    "validations": {
                        "crypto_validation": n.crypto,
                        "tunnel_int_validation": n.tunnel_int,
                        "routing_validation": n.routing,
                        "vrfs_validation": n.vrfs,
                        "tcl_scp_validation": n.tcl_scp,
                        "nat_validation": n.nat,
                        "acl_validation": n.acl,
                        "route_map_validation": n.route_map_prefix_list,
                    },
                    "copp_bw": n.copp_bw,
                    "logging_configured": n.logging_configured,
                    "logging_host": n.logging_host,
                    "logging_level": n.logging_level,
                    "logging_facility": n.logging_facility,
                },
            }

    all_groups = {}
    groups = ["HUB", "SPOKE"]
    for group in groups:
        all_groups[group] = {"data": {"enabled": True}}

    data = {}
    data["groups"] = all_groups
    data["hosts"] = all_hosts
    data["defaults"] = all_defaults
    return data


class Myinventory(Inventory):
    """
    Initiating nornir inventory
    """

    def __init__(self, data, **kwargs):

        defaults = data["defaults"]
        groups = data["groups"]
        hosts = data["hosts"]

        super().__init__(hosts=hosts, groups=groups, defaults=defaults, **kwargs)


def inventory():
    data = get_inventory_data(Defaults, Hosts)
    nr = InitNornir(
        core={"num_workers": 100},
        inventory={"plugin": Myinventory, "options": {"data": data}},
        logging={"enabled": settings.DEBUG},
        jinja2={"filters": "api.helpers.misc.custom_filters"},
    )
    return nr
