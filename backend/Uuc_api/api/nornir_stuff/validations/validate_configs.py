from nornir_scrapli.tasks import send_command as scrape_send
from nornir.plugins.tasks import text
from api.helpers.misc import ParseConfig
import os

def parse_validation_template(
    task, template, option, device_config, spoke_networks_all
):
    normalize_config = [
        x.strip() for x in device_config.splitlines() if len(x) != 0 and x != "!"
    ]
    normalized_config = "\n".join(normalize_config)

    if template == "tcl_scp":
        if task.host.groups[0] == "SPOKE":
            if option == 2:
                return None
            else:
                task.run(task=scrape_send, command="cd nvram:")
                result = task.run(task=scrape_send, command=f"dir").result
                task.host.close_connection("scrapli")
                if f"{task.host.name}.tcl" in result:
                    passed = 0
                    return passed
        else:
            return None

    elif template == "vrfs" and task.host.groups[0] == "HUB":
        return None

    elif template == "nat":
        interfaces_with_nat = []
        interfaces = ParseConfig(device_config).get_parsed("nat_check")
        for interface in interfaces[0][0]:
            try:
                _nat = interface["type"]
                interfaces_with_nat.append(interface)
            except KeyError:
                pass

        if option == 1 and task.host.groups[0] == "SPOKE":
            return None
        else:
            wan_check = None
            lan_check = None
            Tunnel_check = None

            for interface in interfaces_with_nat:
                if interface["interface"] == task.host.data["wan_int"]:
                    if interface["type"] == "outside":
                        wan_check = True

                if (
                    task.host.groups[0] == "HUB"
                    and interface["interface"] == "Tunnel414"
                ):
                    if interface["type"] == "inside":
                        Tunnel_check = True

                for advertised_interface in task.host.data["advertised_interfaces"]:
                    if advertised_interface == interface["interface"]:
                        if interface["type"] == "inside":
                            lan_check = True

            if task.host.groups[0] == "HUB":
                if wan_check == True and lan_check == True and Tunnel_check == True:
                    return 0
                else:
                    return 1

            else:
                if wan_check == True and lan_check == True:
                    return 0
                else:
                    return 1

    else:
        if template == "vrfs" and option == 2:
            return None
        elif template == "route_map_prefix_list" and task.host.groups[0] == "HUB":
            return None
        elif (
            template == "route_map_prefix_list"
            and task.host.groups[0] == "SPOKE"
            and option != 3
        ):
            return None
        elif template == "acl" and task.host.groups[0] == "SPOKE" and option == 1:
            return None
        else:
            parse_template = task.run(
                task=text.template_file,
                template=f"{template}.jinja2",
                path=f"{os.getcwd()}/Uuc_api/api/nornir_stuff/validations/",
                option=option,
                spoke_networks_all=spoke_networks_all,
            )

            configs = [
                x.strip() for x in parse_template.result.splitlines() if x.strip()
            ]
            passed = 0
            for cmd in configs:
                if cmd in normalized_config:
                    continue
                else:
                    passed = 1
                    break

            return passed


def validate(task, option, spoke_networks_all):
    results = {}
    # Get device running-config
    device_config = task.run(task=scrape_send, command="show running-config").result

    task.host.close_connection("scrapli")
    ##############################################################

    validations_to_run = [
        "crypto",
        "tunnel_int",
        "vrfs",
        "tcl_scp",
        "routing",
        "route_map_prefix_list",
        "nat",
        "acl",
    ]

    for validation_to_run in validations_to_run:
        output = task.run(
            task=parse_validation_template,
            template=validation_to_run,
            option=option,
            device_config=device_config,
            spoke_networks_all=spoke_networks_all,
        )
        results[validation_to_run] = output.result

    return results
