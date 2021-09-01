import datetime
import re

import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import subprocess
from concurrent.futures import ProcessPoolExecutor
from nornir_scrapli.tasks import send_command as scrape_send
from nornir_scrapli.tasks import get_prompt
import pysnmp.hlapi.asyncio as snmp
from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp.hlapi as snmp_sync
from .constants import COMMUNITY_STR ,CISCO_OIDS ,FORTINET_OIDS
from api.models import Defaults
from api.helpers.misc import  resolve_host
from api.helpers.inventory_builder import inventory

def test_ssh_conn(task):
    """
    function to test the ssh connectivity
    """
    task.host.platform = "generic"
    alive = False
    try:
        task.host.get_connection("scrapli", task.nornir.config)
        alive = True
        task.host.close_connection("scrapli")
        return alive
    except:
        alive = False
        return alive



def do_ping(nr):
    """function to check reachability of the hosts"""
    status = []
    for device_name in nr.inventory.hosts.keys():
        host = nr.inventory.hosts[device_name].hostname
        name = nr.inventory.hosts[device_name].name

        response = subprocess.Popen(
            ["timeout", "6", "ping", "-c", "2", host], stdout=subprocess.PIPE
        )
        response.wait()
        if response.returncode != 0:
            reach = False
            status.append({"name": name, "reach": reach})
        else:
            reach = True
            status.append({"name": name, "reach": reach})

    return status



def check_conn(task , dest):
    task.run(task=get_prompt)
    if task.host.data['vendor'] == "Cisco":
        command = f"ping {dest} source loopback0"
        r = task.run(
            task=scrape_send, command=command
        ).result

        if "!!" in r:
            return True
        else:
            return False

    else:
        loop_back_ip = task.host.data['loop_back'].split()[0]

        command = f"execute ping {dest}"
        task.run(
            task=scrape_send,
            name="Set Ping Options",
            command=f"execute ping-options source {loop_back_ip}"
        )
        r = task.run(
            task=scrape_send,
            command=command
        ).result
        text = re.findall(r'\d\spackets\sreceived' , r)

        if int(text[0].split()[0]) < 2:
            return False

        else:
            return True





class SNMPManager():

    def __init__(self):
        self.community_str = COMMUNITY_STR
        self.host_ip = None
        self.oid_set = None

    def get_oid_set(self,vendor):
        if vendor == 'cisco':
            return CISCO_OIDS
        elif vendor == 'fortinet':
            return FORTINET_OIDS


    def sync_poll_sys(self ,oids):
        oid_list = [x['OID'] for x in oids]
        result = {}

        ramusage=""
        Cn=0
        Cr=5
        errorIndication, errorStatus, errorIndex, \
            varBindTable = cmdgen.CommandGenerator().bulkCmd(
            cmdgen.CommunityData(self.community_str),
            cmdgen.UdpTransportTarget((self.host_ip, 161)),
            Cn, Cr,
            *oid_list
        )
        result = {}
        
        for var,oid in zip(varBindTable[0],oids):
            output = {}
            o,val = var
            if oid["field"] == "sysUpTime":
                output['uptime'] = str(
                    datetime.timedelta(seconds=int(val) / 100)
                ).split(".")[0]
                result.update(output)

            elif oid['field'] == "sysDescr":
                if 'Cisco' in str(val):
                    output['vendor'] = 'Cisco'
                    output['sysDescr'] = " ".join(str(val).split(",")[1:3])
                elif 'FortiGate' in str(val):
                    output['vendor'] = "Fortinet"
                    output['sysDescr'] = str(val)
                result.update(output)
            else:
                result.update({oid['field']:str(val)})
        
        return result
       

    def get_interfaces(self ,params):
        results = []
        data={}
        try:
            for (errorIndication,
                errorStatus,
                errorIndex,
                varBinds) in snmp_sync.nextCmd(snmp_sync.SnmpEngine(),
                                    snmp_sync.CommunityData(self.community_str),
                                    snmp_sync.UdpTransportTarget((self.host_ip, 161), timeout=1),
                                    snmp_sync.ContextData(),
                                    snmp_sync.ObjectType(snmp_sync.ObjectIdentity(params['OID'])),
                                    lexicographicMode=False):
                for varBind in varBinds:
                    output = [x.prettyPrint() for x in varBind][1]
                    results.append(output)
            data = {params['field']:results}
        except:
            data = {params['field']:[]}

        return data


    def build_interface_table(self ,oids):
        results = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            execute=executor.map(self.get_interfaces ,oids)
            data = list(execute)
            index_desc = list(zip(
                                data[0]["ifDescr"] , data[2]["ifOperStatus"],
                                data[1]["ifIndex"] , data[5]['ifAdminStatus'],
                                data[6]["ifOutOctets"] , data[7]['ifInOctets'],
                                data[8]["ifInErrors"] , data[9]['ifOutErrors'],
                                data[10]["ifPhysAddress"]

                                )
                            )
            index_ip =  list(zip(data[3]["ipAdEntIfIndex"] , data[4]["ipAdEntAddr"]))

            for interface in index_desc:
                interface_result= {
                        "name":interface[0],"status":interface[1] ,  "adminstatus":interface[3],
                        "Out":float("%.2f" % round(int(interface[4]) / 1000000 ,2)),
                        "In":float("%.2f" % round(int(interface[5]) / 1000000,2)) ,
                        "InErrors":interface[6],
                        "OutErrors":interface[7],
                        "mac":interface[8][2:].upper(),
                    }
                for addressed_int in index_ip:
                    if interface[2] == addressed_int[0]:
                        interface_result["ipaddr"] = addressed_int[1]


                if not interface_result.get("ipaddr"):
                    interface_result['ipaddr'] = "unassigned"

                results.append(interface_result)

            return results



    def snmp_get(self ,host):
        self.host_ip = host["IP"]
        self.vendor = host['vendor']

        
        result = {}

        try:
            oids = self.get_oid_set(host['vendor'])['sys_oids']
            response = self.sync_poll_sys(oids)

            result['vendor'] = response['vendor']
            result['fqdn'] = response['fqdn']
            result['uptime'] = response['uptime']
            result['chassisid'] = response['chassisid']
            result['sysDescr'] = response['sysDescr']

            if result['vendor'] == "Cisco":
                divider = 1000000
                totalram = int(response['ciscoMemoryPoolUsed-processor']) + int(response['ciscoMemoryPoolFree-processor'])
                ramusage = float(int(response['ciscoMemoryPoolUsed-processor'])) / float(totalram) *100
            elif result['vendor'] == "Fortinet":
                divider = 1000
                totalram = int(response['totalmemory'])
                ramusage = int(response['usedmemory'])



            result['cpuusage'] = int(response['cpuusage'])
            totalramsize = str(int(totalram / divider)) + "MB"
            result['ramusage'] = float("%.2f" % round(ramusage,2))
            result['totalramsize'] = totalramsize



            result.update({"interfaces":self.build_interface_table(self.get_oid_set(host['vendor'])['interface_oids'])})
            for interface in result['interfaces']:
                if interface['name'] == host['wan_int']:
                    result['wan_ip'] = interface['ipaddr']
                    break
                else:
                    continue

            data = {"name": host["name"], "result": result}
        except:
            data = {"name": host["name"], "result": {'ramusage':0,'cpuusage':0}}


        return data



    def do_poll(self ,hosts, avg=None):
        data=[]
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            execute = executor.map(self.snmp_get ,hosts)
            data = list(execute)

        if avg:
            topdevices = {}
            try:
                topdevices["topramusage"] = sorted(data, key=lambda k: k['result']['ramusage'] , reverse=True)[:5]
                topdevices['topcpuusage'] = sorted(data, key=lambda k: k['result']['cpuusage'] , reverse=True)[:5]
            except:
                topdevices= {"topramusage":[] ,"topcpuusage":[] }

            data = topdevices

        return data


    def get_data(self , hosts , avg=None):
        output = self.do_poll(hosts ,avg=avg)
        return output




class TopologyBuilder():

    def fetch_cdp_data(self,task):
        task.run(task=scrape_send, command="show cdp neighbors")
        task.host.close_connection("scrapli")


    def fortigate_neighbors(task):
        task.run(task=get_prompt)
        if task.host.headend_vendor == "Cisco":
            r = task.run(
                    task=scrape_send, command="get vpn ipsec tunnel summary | grep  HQ_CISCO_VTI"
                ).result
            
            alive = True
            result = r.split()[3]
            if '1/1' not in result:
                alive = False
            return {'tunnel_alive':alive}

        else:
            r = task.run(
                task=scrape_send, command="get vpn ipsec tunnel details | grep remote-gateway"
            ).result

            neighbors = [
                tunnel.split()[1].split(":")[0] for tunnel in r.splitlines() if len(tunnel) != 0
            ]
            neighbors.remove("#")
        return neighbors




    def build_topology(self):
        nr = inventory()

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
        result = nr.run(task=self.fetch_cdp_data)
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
            wan_interface = nr.inventory.hosts[hosts[v]].data['wan_int']
            loop_back =  nr.inventory.hosts[hosts[v]].data['loop_back'].split()[0]

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
                    "title": f"<div class='tooltip-content'><div class='tooltip-element'><h2 style='color:#42A5F5;' >{site_name}<h2> \
                            <hr id='tooltip-hr'></div><div class='tooltip-element'><h3><strong style='margin-right:20px;'>Vendor </strong>   {vendor}</h3> \
                            <h3><strong style='margin-right:20px;'>WAN Interface </strong>   {wan_interface}</h3> \
                            <h3><strong style='margin-right:20px;'>LoopBack </strong>   {loop_back}</h3></div></div>"

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
                        else:
                            pass

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
                            final_edges.append({"from": new_edge["from"], "to": sum_of_devices ,"color":"red","width":1.7})
                            continue
                        for node in nodes:
                            if edge["neighbor"] == node["label"].split(".")[0]:
                                new_edge["to"] = node["id"]

                if edge["type"] == "overlay":
                    if edge["neighbor"] == '':
                        pass
                    final_edges.append({"from": new_edge["from"], "to": sum_of_devices})
                elif edge["type"] == "underlay":
                    pass

        data = {"nodes": nodes, "edges": final_edges}

        data = {"result":data}

        return data



def juniper_neighbors(task):
    r = task.run(
        task=scrape_send, command="show security ike security-associations | grep IKE"
    ).result

    neighbors = [nei.split()[5] for nei in r.splitlines() if len(nei) != 0]
    return neighbors