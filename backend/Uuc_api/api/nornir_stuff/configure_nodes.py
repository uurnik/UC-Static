from time import sleep
import json
import itertools
import re
import os

from django.conf import settings
from api.models import Hosts, Defaults
from nornir.core.filter import F
from nornir.plugins.tasks import networking, text
from netaddr import IPNetwork
import dns.update as dnsupdate
import dns.query as dnsquery
import dns.resolver as dnsresolver
from netaddr import IPNetwork, IPAddress
from ipaddress import IPv4Interface, ip_network, ip_address, ip_interface
from ttp import ttp
from scrapli.driver.core import IOSXEDriver
from scrapli.driver import GenericDriver
from netmiko import file_transfer
from nornir_scrapli.tasks import send_command as scrape_send
from nornir_scrapli.tasks import send_configs as scrape_config
from nornir_scrapli.tasks import send_commands as scrape_config_commands
from nornir_scrapli.tasks import get_prompt
from ..helpers.misc import (
    ParseConfig,
    ForigateParser,
    JuniperParser,
    convert_to_cidr,
    get_challenge_pass,
    low_usr_cmds,
    get_interface_index,
    CoppBWCalculator,
    add_ddns_url,
    resolve_host,
)

if settings.DEBUG:
    import logging
    logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
    logger = logging.getLogger("scrapli")


def netmiko_direct(task, cmd):
    """
    Manually create Netmiko connection, to handle prompts
    clear ip nat translations
    """
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    output = net_connect.send_command("clear ip nat translation *")
    net_connect.config_mode()
    output = net_connect.send_command_timing(cmd)
    if "entries" in output:
        output += net_connect.send_command_timing("yes")
    net_connect.exit_config_mode()
    net_connect.disconnect()
    return output


def scp_file_transfer(task):
    """
    Transfer Tickle Script using netmiko
    """
    net_connect = task.host.get_connection("netmiko", task.nornir.config)
    try:
        _transfer = file_transfer(
            net_connect,
            source_file=f"{task.host.name}.tcl",
            dest_file=f"{task.host.name}.tcl",
            file_system="nvram:/",
            direction="put",
            overwrite_file=True,
        )
    except:
        pass
    net_connect.disconnect()


def send_tcl(task):
    """
    Transfering the tcl script to schedule ip assignment
    """
    # Enable SCP server on the Host
    _en_scp = task.run(task=scrape_config, configs=["ip scp server enable"])
    task.host.close_connection("scrapli")

    # SCP TCL script to the host

    task.run(task=scp_file_transfer)

    # Parse the template to kron schedule the TCL script on the Host
    parse_template = task.run(
        task=text.template_file,
        name="Pasrse tcl schedule template",
        template="kro_schedule.jinja2",
        path=f"api/nornir_stuff/templates/cisco/{task.host.groups[0]}",
    )

    # Push the config to schedule the TCL script
    kron_schedule = task.run(
        task=scrape_config,
        name="Load kron schedule",
        configs=parse_template.result.splitlines(),
    )
    task.host.close_connection("scrapli")

    return kron_schedule


def facts(task):
    """
    function to gather the facts about devices
    1. Check the device Platform and update Hosts table
    2. Gather hostname,interfaces,model,serial_no,os_version ,vendor
    """
    DOMAIN = ".uurnikconnect.com"
    conn = GenericDriver(
        host=task.host.hostname,
        auth_username=task.host.username,
        auth_password=task.host.password,
        timeout_transport=35,
        timeout_socket=35,
        timeout_ops=35,
        transport="ssh2",
        auth_strict_key=False,
        comms_prompt_pattern=r"^(\w+.*?)([#\s,>\s,#])$",
    )

    conn.open()
    conn.get_prompt()
    output = conn.send_command("show version | inc Cisco").result
    conn.send_command("\n")
    conn.close()

    if "command parse error" in output.lower():
        platform = "fortinet"
    elif "cisco nexus" in output.lower():
        platform = "nxos"
    elif "cisco ios xr" in output.lower():
        platform = "iosxr"
    elif "cisco ios xe" in output.lower():
        platform = "ios"
    elif "cisco ios" in output.lower():
        platform = "ios"
    else:
        platform = "junos"

    if platform == "junos":
        task.host.platform = platform
        r = task.run(
            task=scrape_send, command="show version"
        ).scrapli_response.textfsm_parse_output()

        # get serial number
        get_serial_number = task.run(
            task=scrape_send, command="show chassis hardware | grep Chassis"
        ).result.split()[1]

        # get ram size
        get_ram_size = task.run(
            task=scrape_send, command='show system memory | grep "Total memory"'
        ).result.split()[2]

        get_wan_interface = task.run(
            task=scrape_send, command="show interfaces terse"
        ).result

        output = JuniperParser(get_wan_interface).get_parsed(template="all_interfaces")

        for interface in output[0][0]:
            if interface["ip"].split("/")[0] == task.host.hostname:
                wan_subnet = IPNetwork(interface["ip"]).netmask
                wan_interface = interface["interface"]
                break

        get_default_route = task.run(
            task=scrape_send, command="show route 0.0.0.0 | display json"
        ).result
        get_next_hop = json.loads(get_default_route)["route-information"][0][
            "route-table"
        ]
        next_hop = get_next_hop[0]["rt"][0]["rt-entry"][0]["nh"][0]["to"][0]["data"]

        get_interface_names = task.run(
            task=scrape_send, command="show interface terse"
        ).result

        interface_info = JuniperParser(get_interface_names).get_parsed(
            template="interface_names"
        )[0][0]

        interfaces = [interface["interface"] for interface in interface_info]

        if len(get_ram_size) != 0:
            ram_size = round(int(get_ram_size) / 1000)

        dbHost = Hosts.objects.get(name=task.host.name)

        dbHost.vendor = "Juniper"
        dbHost.platform = "junos"
        dbHost.ram_size = str(ram_size) + "MB"
        dbHost.serial_no = get_serial_number
        dbHost.dev_name = r[0]["hostname"]
        dbHost.model = r[0]["model"]
        dbHost.os_version = r[0]["junos_version"]
        dbHost.wan_subnet = wan_subnet
        dbHost.wan_int = wan_interface
        dbHost.next_hop = next_hop
        dbHost.interfaces = ",".join(interfaces)
        dbHost.fqdn = r[0]["hostname"] + DOMAIN

        dbHost.save()

        return r[0]["hostname"] + DOMAIN

    elif platform == "fortinet":
        conn = GenericDriver(
            host=task.host.hostname,
            auth_username=task.host.username,
            auth_password=task.host.password,
            transport="ssh2",
            auth_strict_key=False,
            comms_prompt_pattern=r"^.*?\s?#\s",
        )

        dbHost = Hosts.objects.get(name=task.host.name)
        dbHost.platform = "generic"

        conn.open()
        conn.send_commands(
            ["config system console", "set output standard", "end"]
        ).result
        output = conn.send_command("get system status").result

        # Extract WAN interface Name & Subnet
        output = ForigateParser(output).get_parsed(template="system_info")[0][0]
        output_interface = conn.send_command(
            f"get system interface | grep 'ip: {task.host.hostname}'"
        ).result

        wan_interface = output_interface.split("  ")[0].split(":")[1].strip()
        wan_subnet = output_interface.split("  ")[3].split(":")[1].split()[1].strip()

        # Get All Interfaces
        output_interface_all = conn.send_command(f"get system interface").result
        all_interfaces = ForigateParser(output_interface_all).get_parsed(
            template="all_interfaces"
        )[0][0]
        interface_list = [interface["interface"] for interface in all_interfaces]

        # Get Next-Hop from default route
        next_hop_output = conn.send_command(
            "get router info routing-table static"
        ).result
        next_hop_default = ForigateParser(next_hop_output).get_parsed(
            template="default_next_hop"
        )[0][0]

        # get total RAM size
        get_ram_size = (
            conn.send_command("get system performance status | grep Memory:")
            .result.split()[1]
            .strip("k")
        )
        ram_size = int(get_ram_size) / 1000
        conn.close()

        # If device is a hub then add to NHS list
        if task.host.groups[0] == "HUB":
            defaultsDB = Defaults.objects.get(pk=1)
            if dbHost.tunnel_ip not in defaultsDB.nhs_server:
                defaultsDB.hubs_fqds = defaultsDB.hubs_fqds + "," + dbHost.fqdn
                defaultsDB.nhs_server = (
                    defaultsDB.nhs_server + "," + task.host.data["tunnel_ip"]
                )
                defaultsDB.save()

        # Save facts to DB
        dbHost.ram_size = str(round(ram_size)) + "MB"
        dbHost.wan_int = wan_interface
        dbHost.vendor = "Fortinet"
        dbHost.wan_subnet = wan_subnet
        dbHost.next_hop = next_hop_default["next_hop"]
        dbHost.interfaces = ",".join(interface_list)
        dbHost.serial_no = output["serial_no"]
        dbHost.dev_name = output["hostname"]
        dbHost.os_version = output["os_version"]
        dbHost.model = output["model"]
        dbHost.fqdn = output["hostname"] + DOMAIN
        dbHost.save()

        return output["hostname"] + DOMAIN

    elif platform == "ios":
        task.host.platform = platform
        r = task.run(task=networking.napalm_get, getters=["facts"])
        facts_device = r.result
        task.host.close_connection("napalm")

        # Get RAM size
        try:
            version = task.run(
                task=scrape_send, command="show version | inc bytes of memory"
            ).result

            expression = r"\d*?K/\d*?K"

            pattern = re.compile(expression)
            memory = pattern.findall(version)[0].split("/")

            left_one = int(memory[0].strip("K"))
            right_one = int(memory[1].strip("K"))
            ram_size = round((left_one + right_one) / 1024)
        except:
            ram_size = 512

        # Get WAN interface
        get_interface = task.run(
            task=scrape_send,
            name="Get interface",
            command=f"show ip interface brief | inc {task.host.hostname}",
        )
        task.host["wan_int"] = get_interface.result.split()[0]

        # Get WAN interface subnet
        get_wan_subnet = task.run(
            task=scrape_send,
            name="Get interface Subnet",
            command=f"show interfaces { task.host['wan_int']}  | inc  Internet address",
        )
        netmask = IPNetwork(get_wan_subnet.result.split()[3])
        task.host["wan_int_subnet"] = str(netmask.netmask)

        # Get nexthop from the device (by parsing out default route)
        get_next_hop = task.run(
            task=scrape_send,
            name="GET NEXT HOP FOR DEFAULT ROUTE",
            command="show run | inc ip route 0.0.0.0 0.0.0.0",
        )
        next_hop = get_next_hop.result.split()[4]

        # Close SSH connection manually
        task.host.close_connection("scrapli")

        # Save facts to Database
        dbHost = Hosts.objects.get(name=task.host.name)

        dbHost.wan_int = get_interface.result.split()[0]
        dbHost.wan_subnet = task.host["wan_int_subnet"]
        dbHost.next_hop = next_hop
        dbHost.ram_size = str(ram_size) + "MB"
        dbHost.platform = platform

        dbHost.os_version = (
            facts_device["facts"]["os_version"].split(",")[1].split()[1].split("(")[0]
        )

        dbHost.model = facts_device["facts"]["model"]
        dbHost.vendor = facts_device["facts"]["vendor"]
        dbHost.serial_no = facts_device["facts"]["serial_number"]
        dbHost.dev_name = facts_device["facts"]["hostname"]
        dbHost.interfaces = ",".join(facts_device["facts"]["interface_list"])
        dbHost.fqdn = facts_device["facts"]["hostname"] + DOMAIN

        defaultsDB = Defaults.objects.get(pk=1)
        if task.host.groups[0] == "HUB":
            if dbHost.fqdn not in defaultsDB.hubs_fqds:
                defaultsDB.hubs_fqds = defaultsDB.hubs_fqds + "," + dbHost.fqdn

        defaultsDB.save()
        dbHost.save()

        return facts_device["facts"]["hostname"] + DOMAIN


def device_harderning(task):
    """
    function for building & pushing device hardening commands to hosts
    """
    running_config = task.run(task=scrape_send, command="show running-config")
    interface_config = ParseConfig(running_config.result).get_parsed(temp="interfaces")
    logical_interfaces = []
    interfaces = []
    for interface in interface_config[0][0]:
        if "Loop" in interface["interface"] or "Tunnel" in interface["interface"]:
            logical_interfaces.append(interface)
        else:
            interfaces.append(interface["interface"])

    total_ram_size = int(task.host.data["ram_size"].strip("MB")) * 1000
    reserve_mem = round(total_ram_size * (1 - 0.25))
    reserve_mem = total_ram_size - reserve_mem

    config = task.run(
        task=text.template_file,
        template="hardening_cisco.jinja2",
        path="api/nornir_stuff/templates/cisco",
        interfaces=interfaces,
        logical_interfaces=logical_interfaces,
        reserve_mem=reserve_mem,
    )

    commands = [x.strip() for x in config.result.splitlines() if len(x) != 0]

    task.run(task=scrape_config, name="push hardening configs", configs=commands)

    task.host.close_connection("scrapli")


def configure_copp(task):
    """
    function parses the COPP template and push commands to hosts
    """
    copp_bw = CoppBWCalculator(task.host.data["copp_bw"]).calculate()

    config = task.run(
        task=text.template_file,
        template="copp_cisco_template.jinja2",
        path="api/nornir_stuff/templates/cisco",
        copp_bw=copp_bw,
    )
    commands = [x.strip() for x in config.result.splitlines() if len(x) != 0]

    task.run(task=scrape_config, name="push copp configuration", configs=commands)

    task.host.close_connection("scrapli")


def conf_dmvpn(task, nr, dia, other_services=None, dns=None):
    """
    1. Create configuration backup on control node, configurations are saved to api/backup_configs
    2. Enable archive feature to create a backup of running-config of Host locally
    3. Extract WAN interface name from given IP
    4. Get WAN interface subnet & nexthop from default route
    5. Update inventory
    6. Build configuration template for both HUBS & SPOKES
    7. Push configs to devices
    8. Get SNMP interface Index of Tunnel414
    9. Update DNS
    """

    ################################## Juniper Configuration Starts ###########################################
    if task.host.platform == "junos":

        get_interfaces = task.run(
            task=scrape_send, command="show interfaces terse"
        ).result
        interfaces = JuniperParser(get_interfaces).get_parsed(template="all_interfaces")

        advertised_interfaces = []
        for interface in interfaces[0][0]:
            ip = interface["ip"].split("/")[0]
            mask = interface["ip"].split("/")[1]
            interface_network = IPNetwork(f"{ip}/{mask}").network
            subnet_mask = IPNetwork(f"{ip}/{mask}").netmask
            interface_network = f"{interface_network} {str(subnet_mask)}"
            for route in task.host.data["routes"]:
                if route == interface_network:
                    advertised_interfaces.append(interface["interface"])

        task.host.data["advertised_int"] = advertised_interfaces

        config = task.run(
            task=text.template_file,
            template="advpn.jinja2",
            path=f"api/nornir_stuff/templates/juniper/{ task.host.groups[0] }",
            lan_interfaces=advertised_interfaces,
        )

        commands = [x.strip() for x in config.result.splitlines() if len(x) != 0]

        task.run(task=scrape_config, name="Push juniper configs", configs=commands)
        task.host.close_connection("scrapli")

    ################################# Fortigate Configuration Starts ####################################
    if task.host.platform == "generic":
        task.run(task=facts)
        task.run(task=get_prompt)
        task.run(
            task=scrape_config_commands,
            name="set console length",
            commands=["config system console", "set output standard", "end"],
        )

        # Backup full configuration
        get_config = task.run(
            task=scrape_send, command="show full-configuration"
        ).result
        task.host.close_connection("scrapli")
        with open(
            f"{os.getcwd()}/api/backup_configs/{task.host.name}.cfg", "w"
        ) as file:
            file.write(get_config)

        connect_routes = task.run(
            task=scrape_send, command="get system interface"
        ).result
        task.host.close_connection("scrapli")
        interface_parser = ForigateParser(connect_routes).get_parsed(
            template="interface_attr"
        )

        advertised_interfaces = []
        for interface in interface_parser[0][0]:
            ip = interface.get("ip")
            mask = interface.get("mask")
            if ip != None and "169.254" not in ip and "0.0.0.0" not in ip:
                interface_network = IPNetwork(f"{ip}/{mask}").network
                for route in task.host.data["routes"]:
                    if f"{interface_network} {mask}" == route:
                        advertised_interfaces.append(interface["port"])
        task.host.data["advertised_int"] = advertised_interfaces

        config = task.run(
            task=text.template_file,
            template="advpn_main.jinja2",
            path=f"api/nornir_stuff/templates/fortigate/{ task.host.groups[0] }",
            advertised_interfaces=advertised_interfaces,
        )

        commands = [x.strip() for x in config.result.splitlines() if len(x) != 0]
        task.run(
            task=scrape_config_commands, name="forigate advpn config", commands=commands
        )
        task.host.close_connection("scrapli")

        try:
            update = dnsupdate.Update("uurnikconnect.com")
            update.replace(task.host.data["dev_name"], 300, "A", task.host.hostname)
            _response = dnsquery.tcp(update, dns, timeout=20)
        except:
            pass
    ###################################################################################################

    ################################## Cisco Configuration Starts #####################################
    if task.host.platform == "ios":
        # Get running configuration of the Host & save it the backup_configs directory
        # task.run(task=facts)

        get_configs = task.run(
            task=scrape_send,
            name="Backup configurations",
            command="show running-config",
        )

        with open(
            f"{os.getcwd()}/api/backup_configs/{task.host.name}.cfg", "w"
        ) as file:
            file.write(get_configs.result)

        # Enable Archive feature on the device to create a configuration backup on the device
        parse_archive = task.run(
            task=text.template_file,
            name="Parse archive_en template",
            template="archive_en.jinja2",
            path=f"api/nornir_stuff/templates/cisco",
        )
        task.host["archive"] = parse_archive.result

        _en_archive = task.run(
            task=scrape_config,
            name="Push archive config",
            configs=parse_archive.result.splitlines(),
        )

        # # Create a list of Spoke Networks
        spokes_tunnel = []
        loop_backs = []
        spoke_networks = []
        custom_routes = []
        spokes = nr.filter(F(groups__contains="SPOKE"))
        for n in spokes.inventory.hosts.keys():
            spokes_tunnel.append(spokes.inventory.hosts[n].data["tunnel_ip"])
            loop_backs.append(spokes.inventory.hosts[n].data["loop_back"])
            spoke_networks.append(spokes.inventory.hosts[n].data["routes"])
            custom_routes.append(spokes.inventory.hosts[n].data["custom_routes"])

        spoke_networks = [item for sublist in spoke_networks for item in sublist]
        custom_routes = [item for sublist in custom_routes for item in sublist]
        ######################################################################
        advertised_routes = task.host.data["routes"]

        interface_parser = ParseConfig(get_configs.result).get_parsed("interfaces")
        all_interfaces = []
        for interface in interface_parser[0][0]:
            ip = interface.get("address")
            mask = interface.get("mask")
            if ip != None:
                all_interfaces.append(interface)

        advertised_interfaces = []
        for interface in all_interfaces:
            ip = interface.get("address")
            mask = interface.get("mask")
            interface_network = IPNetwork(f"{ip}/{mask}").network
            for route in advertised_routes:
                if f"{interface_network} {mask}" == route:
                    advertised_interfaces.append(interface)

        task.host.data["advertised_int"] = [
            interface_name.get("interface") for interface_name in advertised_interfaces
        ]

        get_static = task.run(task=scrape_send, command="show run | inc ip route")
        task.host["static_routes"] = get_static.result

        routes_to_change = []
        for route in get_static.result.splitlines():
            if route.split(" ")[2] != "0.0.0.0":
                for advertised_route in advertised_routes:
                    static_route = f"{route.split(' ')[2]} {route.split(' ')[3]}"
                    if static_route == advertised_route:
                        routes_to_change.append(route)
        #########################################################################
        spoke_networks_all = itertools.chain(loop_backs, spoke_networks, custom_routes)

        # Get only connected networks and interface IP
        connected_networks = []
        for interface in task.host.data["advertised_int"]:
            output = (
                task.run(
                    task=scrape_send,
                    command=f"show interface {interface} | inc Internet address",
                )
                .result.strip()
                .split()[3]
            )
            ip = output.split("/")[0]
            mask = output.split("/")[1]
            network = str(IPNetwork(output).network)
            connected_networks.append({"network": network + "/" + mask, "ip": ip})

        # ######################################################

        # add ddns update method on device
        task.run(task=add_ddns_url, dns=dns)

        # Parse the main confiuguration template
        parse_template = task.run(
            task=text.template_file,
            name="Base Configuration",
            template="mytemplate.jinja2",
            path=f"api/nornir_stuff/templates/cisco/{task.host.groups[0]}",
            neighbors=spokes_tunnel,
            loop_backs=loop_backs,
            spoke_networks=spoke_networks,
            custom_routes=custom_routes,
            dia=dia,
            dns=dns,
            other_services=other_services,
            low_usr_cmds=low_usr_cmds,
            connected_networks=connected_networks,
        )

        task.host["config"] = parse_template.result
        config = [x.strip() for x in parse_template.result.splitlines() if len(x) != 0]

        # Push config
        task.run(task=scrape_config, name="Loading configuration", configs=config)
        task.host.close_connection("scrapli")

        # configure device hardening and COPP if already deployed on network
        sleep(3)
        if task.host.defaults.data["is_device_hardening_configured"] == True:
            task.run(task=device_harderning)
            sleep(3)
        if task.host.defaults.data["is_copp_configured"] == True:
            task.run(task=configure_copp)
            sleep(3)

        # Push NAT configuration on the Host according to the access type
        if task.host.groups[0] == "SPOKE":
            if dia == "y" or other_services == "y":
                task.run(
                    task=scrape_config,
                    name="Configure NAT on WAN",
                    configs=[f"int {task.host.data['wan_int']}", "ip nat outside"],
                )

        if task.host.groups[0] == "HUB":
            task.run(
                task=scrape_config,
                name="Configure NAT on WAN",
                configs=[f"int {task.host.data['wan_int']}", "ip nat outside"],
            )

        #####################################################################
        if dia != "y" and task.host.groups[0] == "SPOKE":
            pass
        else:
            ip_nat_parse_template = task.run(
                task=text.template_file,
                template="ip_nat_inside.jinja2",
                path="api/nornir_stuff/templates/cisco",
                advertised_interfaces=advertised_interfaces,
            )

            task.run(
                task=scrape_config,
                name="NAT inside configuration",
                configs=ip_nat_parse_template.result.splitlines(),
            )

        if task.host.groups[0] == "SPOKE":
            if other_services == "y":
                vrf_parse_template = task.run(
                    task=text.template_file,
                    template="configure_vrf_LAN.jinja2",
                    path="api/nornir_stuff/templates/cisco/SPOKE",
                    advertised_interfaces=advertised_interfaces,
                )

                task.run(
                    task=scrape_config,
                    name="vrf LAN configuration",
                    configs=vrf_parse_template.result.splitlines(),
                )
                if len(routes_to_change) != 0:
                    static_route_vrf_template = task.run(
                        task=text.template_file,
                        template="change_static_route.jinja2",
                        path="api/nornir_stuff/templates/cisco",
                        routes_to_change=routes_to_change,
                    )

                    task.run(
                        task=scrape_config,
                        name="vrf LAN route configuration",
                        configs=static_route_vrf_template.result.splitlines(),
                    )
        try:
            task.host.close_connection("scrapli")
        except:
            pass
        ####################################################################

        # Create TCL script with Host name as the filename of the TCL script, SCP to the Host and schedule to assign vrf and put IP address again
        if dia == "n" and task.host.groups[0] == "SPOKE":
            tcl_script = f'tclsh\n ios_config "interface {task.host.data["wan_int"]}" "ip vrf forwarding INTERNET" "ip address {task.host.hostname} {task.host.data["wan_subnet"]}" "exit" "interface tunnel 414" "shutdown" "no shutdown" \n tclquit'
            with open(task.host.name + ".tcl", "w") as f:
                f.write(tcl_script)
            task.run(task=send_tcl)
            os.remove(f"{task.host.name}.tcl")

        # get snmp interface index (1.3.6.1.2.1.2.2.1.2.x)
        interface_index = get_interface_index(task.host.hostname, "public", "Tunnel414")
        task.host.data["interface_index"] = interface_index

        # Update dns server
        try:
            update = dnsupdate.Update("uurnikconnect.com")
            update.replace(task.host.data["dev_name"], 300, "A", task.host.hostname)
            _response = dnsquery.tcp(update, dns, timeout=10)
        except:
            pass

        return list(spoke_networks_all)
    ##################################################################################################


def remove_hosts(task):
    """
    function for defining the method to remove configuration on Hosts
    """
    # Get the access type
    option = task.host.defaults.data["access_type"]

    if task.host.platform == "junos":
        parse_template = task.run(
            task=text.template_file,
            name="Parse Juniper Configuration removal",
            template="remove_config.jinja2",
            path=f"api/nornir_stuff/templates/juniper/{task.host.groups[0]}",
        )
        config = [x.strip() for x in parse_template.result.splitlines() if len(x) != 0]
        task.run(task=scrape_config, name="Remove Configuration", configs=config)
        task.host.close_connection("scrapli")

    if task.host.platform == "generic":
        parse_template = task.run(
            task=text.template_file,
            name="Prarse Fortigate Configuration removal",
            template="remove_config.jinja2",
            path=f"api/nornir_stuff/templates/fortigate/{task.host.groups[0]}",
        )
        config = [x.strip() for x in parse_template.result.splitlines() if len(x) != 0]
        task.run(
            task=scrape_config_commands, name="Remove Configuration", commands=config
        )
        task.host.close_connection("scrapli")

    if task.host.platform == "ios":
        get_interface = task.run(
            task=scrape_send, command="show run | sec interface"
        ).result

        interface_parser = ParseConfig(get_interface).get_parsed(temp="interfaces")

        advertised_int = []
        for interface in interface_parser[0][0]:
            for advertised_interface in task.host.data["advertised_interfaces"]:
                if interface["interface"] == advertised_interface:
                    ip = interface["address"]
                    mask = interface["mask"]
                    advertised_int.append(
                        {"name": interface["interface"], "ip": ip, "mask": mask}
                    )

        get_static = task.run(task=scrape_send, command="show run | inc ip route")

        routes = task.host.data["routes"]
        static_routes = []

        if task.host.groups[0] == "SPOKE":
            for static_route in get_static.result.splitlines():
                if static_route.split(" ")[2] != "0.0.0.0":
                    for route in routes:
                        if route in static_route:
                            if "vrf LAN" in static_route:
                                static = static_route.split(" ")
                                static_routes.append(
                                    f"{static[4]} {static[5]} {static[6]}"
                                )
        else:
            for static_route in get_static.result.splitlines():
                if static_route.split(" ")[2] != "0.0.0.0":
                    for route in routes:
                        if route in static_route:
                            static = static_route.split(" ")
                            static_routes.append(f"{static[2]} {static[3]} {static[4]}")

        # Parse the remove config template
        parse_template = task.run(
            task=text.template_file,
            name="Base Configuration",
            template="remove_config.jinja2",
            path=f"api/nornir_stuff/templates/cisco",
            option=option,
            advertised_int=advertised_int,
            static_routes=static_routes,
            low_usr_cmds=low_usr_cmds,
        )
        config = [x.strip() for x in parse_template.result.splitlines() if len(x) != 0]

        # Push the remove config to the Host
        task.run(
            task=scrape_config, name="Remove Configuration from Spoke", configs=config
        )
        task.host.close_connection("scrapli")

        # Run the netmiko direct function which will first remove the NAT translations and then remove ip nat configuration
        if task.host.groups[0] == "SPOKE" and option != 2:
            pass
        else:
            cmd = f"no ip nat inside source list uurnik interface {task.host.data['wan_int']} overload"
            task.run(task=netmiko_direct, cmd=cmd)

        # Check if COPP is configured ,if yes then remove COPP configuration
        if task.host.defaults.data["is_copp_configured"] == True:
            with open("api/nornir_stuff/templates/cisco/remove_copp.txt") as file:
                file_data = file.read()
                commands = [x for x in file_data.splitlines()]
                task.run(task=scrape_config, configs=commands)
        try:
            task.host.close_connection("scrapli")
        except:
            pass

        # Create a TCL script to remove the INTERNET vrf and put ip address on that interface again
        if option == 1 or option == 3:
            if task.host.groups[0] == "SPOKE":
                tcl_script = f'tclsh\n ios_config "interface {task.host.data["wan_int"]}" "no ip vrf forwarding INTERNET" "ip address {task.host.hostname} {task.host.data["wan_subnet"]}" "exit" "no ip vrf INTERNET 0.0.0.0 0.0.0.0 {task.host.data["next_hop"]}" "no ip vrf INTERNET"\ntclquit '
                with open(task.host.name + ".tcl", "w") as f:
                    f.write(tcl_script)
                task.run(task=send_tcl)
                os.remove(f"{task.host.name}.tcl")


def change_on_spoke(task, option, hub_tunnel_ip, hub_nbma):
    """
    function to add static hub mapping & BGP neighborship
    """
    r = task.run(
        task=text.template_file,
        template="add_hub.jinja2",
        path=f"api/nornir_stuff/templates/cisco/{task.host.groups[0]}",
        hub_tunnel_ip=hub_tunnel_ip,
        hub_nbma=hub_nbma,
        option=option,
    )

    configs = [x.strip() for x in r.result.splitlines() if len(x) != 0]
    task.run(
        task=scrape_config, name="add nhs entry & bgp neighborship", configs=configs
    )
    task.host.close_connection("scrapli")


def remove_hub_from_spoke(task, option, hub_tunnel_ip, hub_nbma):
    """
    function to remove static hub mapping & BGP neighborship
    """
    r = task.run(
        task=text.template_file,
        template="remove_hub.jinja2",
        path=f"api/nornir_stuff/templates/cisco/{task.host.groups[0]}",
        hub_tunnel_ip=hub_tunnel_ip,
        hub_nbma=hub_nbma,
        option=option,
    )

    task.run(
        task=scrape_config,
        name="remove nhs entry & bgp neighborship",
        configs=r.result.splitlines(),
    )
    task.host.close_connection("scrapli")


def conf_ip_sla(task, track_ip):
    """
    function to configure ip sla and hsrp tracking

        :params:
            track_ip: ip to track for sla
    """
    ospf_is_routing_proto = task.run(
        task=scrape_send, command="show run | inc router ospf"
    )
    if len(ospf_is_routing_proto.result) != 0:
        ospf = True
        ospf_proc_id = ospf_is_routing_proto.result.split()[2]
    else:
        ospf = False
        ospf_proc_id = False

    eigrp_is_routing_proto = task.run(
        task=scrape_send, command="show run | inc router eigrp"
    )
    if len(eigrp_is_routing_proto.result) != 0:
        eigrp = True
        eigrp_as_num = eigrp_is_routing_proto.result.split()[2]
    else:
        eigrp = False
        eigrp_as_num = False

    rip_routing_proto = task.run(task=scrape_send, command="show run | inc router rip")
    if len(rip_routing_proto.result) != 0:
        rip = True
    else:
        rip = False

    r = task.run(
        task=text.template_file,
        template="ip_sla.jinja2",
        path=f"api/nornir_stuff/templates/cisco",
        track_ip=track_ip,
        ospf=ospf,
        ospf_proc_id=ospf_proc_id,
        eigrp=eigrp,
        eigrp_as_num=eigrp_as_num,
        rip=rip,
    )

    task.host["config"] = r.result
    config = [x.strip() for x in r.result.splitlines() if len(x) != 0]

    task.run(
        task=scrape_config, name="configure ip sla and hsrp tracking", configs=config
    )

    task.host.close_connection("scrapli")


def fetch_cdp_data(task):
    """
    function to get CDP Neighbors information
    by exec "show cdp neighbors"
    """
    task.run(task=scrape_send, command="show cdp neighbors")
    task.host.close_connection("scrapli")


def get_routing_table_cisco(task):
    r = task.run(task=scrape_send, command="show ip route")
    return r.scrapli_response.textfsm_parse_output()


def get_routes(task):
    """
    ( Cisco devices)
        1. Get 'Show run | sec interface' output
        2. Get 'Show run | inc ip route' output
    (Fortigate devices)
        1. Get "get system interface"
    """
    # for juniper
    if task.host.platform == "junos":
        get_interfaces = task.run(
            task=scrape_send, command="show interfaces terse"
        ).result

        connected_interfaces = JuniperParser(get_interfaces).get_parsed(
            template="all_interfaces"
        )

        routes = []
        for interface in connected_interfaces[0][0]:
            if ip_address(interface["ip"].split("/")[0]).is_private == True:
                if "127.0." not in interface["ip"]:
                    route = IPNetwork(interface["ip"]).network
                    cidr = interface["ip"].split("/")[1]
                    route_f = f"{route}/{cidr}"
                    routes.append(route_f)

        return routes

    # for Cisco
    if task.host.platform == "ios":
        connect_routes = task.run(
            task=scrape_send, command="show run | sec interface"
        ).result

        static_routes = task.run(
            task=scrape_send, command="show run | inc ip route"
        ).result

        dynamic_routes = task.run(task=scrape_send, command="show ip route")
        task.host.close_connection("scrapli")

        routes = []
        try:
            for route in dynamic_routes.scrapli_response.textfsm_parse_output():
                if "O" in route["protocol"] or "D" in route["protocol"]:
                    routes.append(f"{route['network']}/{route['mask']}")
        except:
            pass

        interface_parser = ParseConfig(connect_routes).get_parsed(temp="interfaces")

        for interface in interface_parser[0][0]:
            ip = interface.get("address")
            mask = interface.get("mask")
            if ip != None:
                if ip_address(ip).is_private == True:
                    route = IPNetwork(f"{ip}/{mask}").network
                    route = f"{route}/{convert_to_cidr(mask)}"
                    routes.append(route)

        for static_route in static_routes.splitlines():
            line = static_route.split(" ")
            network = line[2]
            subnet = line[3]
            route = f"{network}/{convert_to_cidr(subnet)}"
            if network != "0.0.0.0":
                routes.append(route)

        return routes

    # For fortigate
    if task.host.platform == "generic":
        task.run(
            task=scrape_config_commands,
            name="forigate advpn config",
            commands=["config system console", "set output standard", "end"],
        )

        connect_routes = task.run(
            task=scrape_send, command="get system interface"
        ).result

        interface_parser = ForigateParser(connect_routes).get_parsed(
            template="interface_attr"
        )

        routes = []
        for interface in interface_parser[0][0]:
            ip = interface.get("ip")
            mask = interface.get("mask")
            if ip != None and "169.254" not in ip and "0.0.0.0" not in ip:
                if ip_address(ip).is_private == True:
                    route = IPNetwork(f"{ip}/{mask}").network
                    route = f"{route}/{convert_to_cidr(mask)}"
                    routes.append(route)

        task.host.close_connection("scrapli")

        return routes


def fetch_interface_info(task):
    """
    function return the  interface information
    """

    if task.host.platform == "junos":
        get_interfaces = task.run(
            task=scrape_send, command="show interfaces terse"
        ).result

        interfaces = JuniperParser(get_interfaces).get_parsed(template="front_intf")[0][
            0
        ]

        intf_info = []
        for interface in interfaces:
            extra = interface.pop("extra")
            try:
                ip = extra.split()[2]
            except IndexError:
                ip = " "

            interface.update({"ip": ip})
            intf_info.append(interface)

        return intf_info

    if task.host.platform == "ios":
        interfaces = task.run(
            task=scrape_send, command="show ip interface brief"
        ).scrapli_response.textfsm_parse_output()
        task.host.close_connection("scrapli")
        return interfaces

    if task.host.platform == "generic":

        task.run(
            task=scrape_config_commands,
            name="set console length",
            commands=["config system console", "set output standard", "end"],
        )

        raw_interfaces = task.run(
            task=scrape_send, command="get system interface"
        ).result
        task.host.close_connection("scrapli")

        raw_interfaces = ForigateParser(raw_interfaces).get_parsed(
            template="txtfsm_struct_intf"
        )[0][0]

        interfaces = []
        for intf in raw_interfaces:
            intf.pop("mask")
            intf.pop("extras")
            intf.pop("mode")
            interfaces.append(intf)

        return interfaces


def fortigate_neighbors(task):
    task.run(task=get_prompt)

    r = task.run(
        task=scrape_send, command="get vpn ipsec tunnel details | grep remote-gateway"
    ).result

    neighbors = [
        tunnel.split()[1].split(":")[0] for tunnel in r.splitlines() if len(tunnel) != 0
    ]
    neighbors.remove("#")
    return neighbors


def juniper_neighbors(task):
    r = task.run(
        task=scrape_send, command="show security ike security-associations | grep IKE"
    ).result

    neighbors = [nei.split()[5] for nei in r.splitlines() if len(nei) != 0]
    return neighbors


def change_ipsec_keys(task, new_key):
    """
    function for changing IPsec keys (Cisco)
    """

    if task.host.defaults.data["access_type"] == 2:
        cmds = [
            f'no crypto isakmp key {task.host.defaults.data["ipsec_key"]} address 0.0.0.0',
            f"crypto isakmp key {new_key} address 0.0.0.0",
        ]
    if task.host.defaults.data["access_type"] != 2:
        if task.host.groups[0] == "HUB":
            cmds = [
                f'no crypto isakmp key  {task.host.defaults.data["ipsec_key"]} address 0.0.0.0',
                f"crypto isakmp key {new_key} address 0.0.0.0",
            ]
        elif task.host.groups[0] == "SPOKE":
            cmds = [
                "crypto keyring DMVPN vrf INTERNET",
                f'no pre-shared-key address 0.0.0.0 0.0.0.0 key  {task.host.defaults.data["ipsec_key"]}',
                f"pre-shared-key address 0.0.0.0 0.0.0.0 key {new_key}",
            ]

    task.run(task=scrape_config, configs=cmds)
    task.host.close_connection("scrapli")


def configure_logging(task, logging_host, logging_level, facility):
    """
    function for configuring logging on cisco devices
    """
    parse_template = task.run(
        task=text.template_file,
        name="Configure Logging",
        template="logging.jinja2",
        path=f"api/nornir_stuff/templates/cisco/",
        logging_host=logging_host,
        logging_level=logging_level,
        facility=facility,
    )

    cmds = [x.strip() for x in parse_template.result.splitlines()]

    task.run(task=scrape_config, configs=cmds)
    task.host.close_connection("scrapli")
