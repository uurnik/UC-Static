import subprocess
import datetime
import time
import os
import re
import asyncio
from api.models import Hosts

import dns.update as dnsupdate
import dns.query as dnsquery
import dns.resolver as dnsresolver

from netaddr import IPAddress
from ttp import ttp
from scrapli.driver.core import JunosDriver
from requests_ntlm2 import HttpNtlmAuth
import requests
from bs4 import BeautifulSoup

import pysnmp.hlapi.asyncio as snmp
import pysnmp.hlapi as snmp_sync
from scrapli.driver.core import IOSXEDriver
from nornir_scrapli.tasks import send_command as scrape_send
from nornir_scrapli.tasks import get_prompt
from .interface_table_snmp import interface_poll

############# Custom filters ###################
def wildcard_conversion(subnet):
    """
    filter to convert subnetmask to wildcard
    """
    wildcard = []
    for x in subnet.split("."):
        component = 255 - int(x)
        wildcard.append(str(component))
    wildcard = ".".join(wildcard)
    return wildcard


def convert_to_cidr(subnet):
    """
    filter to convert subnet mask to CIDR
    """
    cidr = IPAddress(subnet).netmask_bits()
    return cidr


def custom_filters():
    """
    Return all available filter to nornir
    """
    return {
        "convert_to_wildcard": wildcard_conversion,
        "convert_to_cidr": convert_to_cidr,
    }

def create_response(nr, result):
    data = []
    for host in nr.inventory.hosts.keys():
        data.append(
            {
                nr.inventory.hosts[host].name: {
                    "changed": result[host].changed,
                    "failed": result[host].failed,
                }
            }
        )
        return data


class ParseConfig:
    """
    ttp parsers for Cisco
    """

    interface_template = """
interface {{ interface }}
 ip address {{ address }} {{ mask }}
"""
    default_route_template = """
ip route 0.0.0.0 0.0.0.0 {{ nexthop }}
"""

    get_static_route_template = """
ip route {{ netid }} {{ mask }} {{ nexthop }}
"""

    check_nat_config = """
interface {{ interface }}
 ip nat {{ type }}
"""

    def __init__(self, config):
        self.config = config

    def get_parsed(self, temp):
        if temp == "interfaces":
            template = self.interface_template
        elif temp == "default_route":
            template = self.default_route_template
        elif temp == "static_routes":
            template = self.get_static_route_template
        elif temp == "nat_check":
            template = self.check_nat_config
        else:
            return "pass valid option"

        parser = ttp(data=self.config, template=template)
        parser.parse()
        results = parser.result()
        return results


class ForigateParser:
    """
    ttp parsers for Fortigate devices
    """

    system_status_template = """
Version: {{ model }} {{ os_version }},{{ build }},{{ num }} {{ a }}
Hostname: {{ hostname }}
Serial-Number: {{ serial_no }}
"""
    interface_all_template = """
== [ {{ interface }} ]
"""
    default_next_hop_temp = """
S*    {{ default }} {{ distance }} via {{ next_hop }}, {{ port }}
"""
    interface_attr_template = """
name: {{ port }}  mode: {{ mode }}   ip: {{ ip }} {{ mask }} status: {{ status }}  {{ extras | _line_ }}
"""

    struct_txtfsm_interfaces = """
name: {{ intf }}  mode: {{ mode }}   ip: {{ ipaddr }} {{ mask }} status: {{ status }}  {{ extras | _line_ }}
"""

    def __init__(self, config):
        self.config = config

    def get_parsed(self, template):
        if template == "all_interfaces":
            template = self.interface_all_template
        elif template == "system_info":
            template = self.system_status_template
        elif template == "default_next_hop":
            template = self.default_next_hop_temp
        elif template == "interface_attr":
            template = self.interface_attr_template
        elif template == "txtfsm_struct_intf":
            template = self.struct_txtfsm_interfaces

        parser = ttp(data=self.config, template=template)
        parser.parse()
        results = parser.result()
        return results


class JuniperParser:
    interface_name_template = """
{{ interface | notequal('Interface') }} {{ extra | _line_ }}
"""

    interface_template = """
{{ interface | notequal('Interface') }} {{ admin_status }} {{ link_status }} {{ protocol }} {{ ip | PREFIX }}
"""

    interface_front_template = """
{{ interface | notequal('Interface') }} {{ status }} {{ extra | _line_ }}
"""

    def __init__(self, config):
        self.config = config

    def get_parsed(self, template):
        if template == "all_interfaces":
            template = self.interface_template
        elif template == "interface_names":
            template = self.interface_name_template
        elif template == "front_intf":
            template = self.interface_front_template

        parser = ttp(data=self.config, template=template)
        parser.parse()
        results = parser.result()
        return results


class CoppBWCalculator:
    """
    Bandwidth caculator for Control Place Policing (Cisco)
    """

    ipv6_cp = 0.106
    undesireable_cp_ipv6 = 0.0008
    undesireable_ip_ipv4 = 0.0008
    routing_cp_ipv4 = 0.159
    routing_cp_ipv6 = 0.159
    management_cp = 0.212
    normal_cp_ipv4 = 0.0795
    normal_cp_ipv6 = 0.0795
    isakmp_esp_ah_cp = 0.0159
    catch_all_ipv4 = 0.0795
    catch_all_ipv6 = 0.0795
    class_default = 0.0286

    bw_percent_classes = [
        ipv6_cp,
        undesireable_cp_ipv6,
        undesireable_ip_ipv4,
        routing_cp_ipv4,
        routing_cp_ipv6,
        management_cp,
        normal_cp_ipv4,
        normal_cp_ipv6,
        isakmp_esp_ah_cp,
        catch_all_ipv4,
        catch_all_ipv6,
        class_default,
    ]

    def __init__(self, bw):
        self.bw = int(bw) * 1000000
        # if router throughput is less than 500mbps then CP BW = 5mbps
        # if router throughput is greater than 500mbps and less than 1gig then CP BW = 10mbps
        # if router throughput is greater than 1gig then CP BW = 25mbps
        if self.bw < 500000000:
            self.bw = 5000000
        elif self.bw >= 500000000 and self.bw < 1000000000:
            self.bw = 10000000
        elif self.bw >= 1000000000:
            self.bw = 25000000

    def calculate(self):
        calculated_results = []
        for bw_class in self.bw_percent_classes:
            cp_bw = self.bw * (1 - bw_class)
            cp_bw = self.bw - cp_bw
            if cp_bw < 8000:
                cp_bw = 8000
                cp_burst = cp_bw / 8
                cp_exceeded = cp_burst
                if cp_burst < 1500:
                    cp_burst = 1500
                    cp_exceeded = cp_burst
            else:
                cp_burst = cp_bw / 8
                cp_exceeded = cp_burst
                if cp_burst < 1500:
                    cp_burst = 1500
                    cp_exceeded = cp_burst

            class_all_values = {
                "cp_bw": int(cp_bw),
                "cp_burst": int(cp_burst),
                "cp_exceeded": int(cp_exceeded),
            }

            calculated_results.append(class_all_values)
        return calculated_results


def get_challenge_pass(task):
    auth = HttpNtlmAuth("u_ndes", "Ccie@2016")
    response = requests.get("http://192.168.100.63/certsrv/mscep_admin/", auth=auth)
    soup = BeautifulSoup(response.content)
    template = re.compile(r"The enrollment challenge password is: <b> [A-Z0-9]+ ")
    output = template.findall(str(soup))
    if len(output) == 0:
        print("failed")
    else:
        challenge_pass = output[0].split("<b>")[1].strip()
        print(challenge_pass)

        conn = JunosDriver(
            host=task.host.hostname,
            auth_username=task.host.username,
            auth_password=task.host.password,
            auth_strict_key=False,
            transport="ssh2",
            timeout_ops=35,
            timeout_socket=35,
            timeout_transport=35,
        )
        conn.open()
        prompt = conn.get_prompt()

        pki_commands = [
            "set security pki ca-profile advpn ca-identity uaada enrollment url http://192.168.100.63/certsrv/mscep/mscep.dll",
            "set security pki ca-profile advpn revocation-check disable crl url http://192.168.100.63/CertEnroll/uaadca.crl",
            "commit",
        ]

        conf_pki = conn.send_configs(pki_commands).result
        print(conf_pki)
        output = conn.send_interactive(
            [
                (
                    "request security pki ca-certificate enroll ca-profile advpn",
                    "Do you want to load the above CA certificate ? [yes,no] (no)",
                ),
                ("yes", prompt),
                (
                    f"request security pki generate-key-pair certificate-id {task.host.name}",
                    prompt,
                ),
                (
                    f'request security pki local-certificate enroll ca-profile advpn certificate-id {task.host.name} domain-name {task.host.data["dev_name"]}.uurnik.local email info@uurnik.local ip-address {task.host.hostname} subject DC=uurnik.local,CN={ task.host.data["dev_name"] },OU=IT,O="uurnik systems",L=ISB,ST=FED,C=PK challenge-password {challenge_pass}',
                    prompt,
                ),
            ]
        )
        print(output.result)


low_usr_cmds = [
    "show access-list",
    "show crypto",
    "show ip",
    "show bgp",
    "show line",
    "show dhcp",
    "show control-plane",
    "show clock",
    "show ntp",
    "show history",
    "show hosts",
    "show inventory",
    "show platform",
    "show cdp",
    "show lldp",
    "show snmp",
    "show version",
    "show nhrp",
]


def get_interface_index(host, community_str, int_name):
    snmp_engine = snmp_sync.SnmpEngine()
    for n in range(1, 15):
        try:
            response = snmp_sync.getCmd(
                snmp_engine,
                snmp_sync.CommunityData(community_str),
                snmp_sync.UdpTransportTarget((host, 161), timeout=1),
                snmp_sync.ContextData(),
                snmp_sync.ObjectType(
                    snmp_sync.ObjectIdentity(f"1.3.6.1.2.1.2.2.1.2.{n}")
                ),
            )

            _errorIndication_out, _errorStatus_out, _errorIndex_out, varBinds = list(
                response
            )[0]
            if int_name in str(varBinds[0]):
                return n
            else:
                continue
        except:
            return None

    snmp_engine.transportDispatcher.closeDispatcher()


async def snmp_get(host, community_str):
    
    oids = [
        {
            "field": "sysDescr",
            "OID": "1.3.6.1.2.1.1.1.0",
        },
        {
            "field": "ciscoMemoryPoolUsed-processor",
            "OID": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
        },
        {
            "field": "ciscoMemoryPoolFree-processor",
            "OID": "1.3.6.1.4.1.9.9.48.1.1.1.6.1",
        },
        {"field": "cpmCPUTotal5minRev", "OID": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"},
        {"field": "cpmCPUTotalminRev", "OID": "1.3.6.1.4.1.9.9.109.1.1.1.1.7.1"},
        {"field": "sysUpTime", "OID": "1.3.6.1.2.1.1.3.0"},
        {"field": "WANCounter_in", "OID": "1.3.6.1.2.1.2.2.1.16"},
        {"field": "WANCounter_out", "OID": "1.3.6.1.2.1.2.2.1.10"},
        {"field": "fqdn","OID":"1.3.6.1.2.1.1.5.0"},
        {"field": "chassisid","OID":"1.3.6.1.4.1.9.3.6.3.0"}
    ]

    result = {}
    snmp_engine = snmp.SnmpEngine()
    host["int_index"] = "1"


    try:
        for oid in oids:
            if "WANCounter" in oid["field"]:
                oid["OID"] = oid["OID"] + "." + str(host["int_index"])

            response = await snmp.getCmd(
                snmp_engine,
                snmp.CommunityData(community_str),
                snmp.UdpTransportTarget((host["IP"], 161), timeout=1),
                snmp.ContextData(),
                snmp.ObjectType(snmp.ObjectIdentity(oid["OID"])),
            )

            _errorIndication, _errorStatus, _errorIndex, varBinds = response

            ramusage=""
            for varBind in varBinds:
                output = {oid["field"]: [x.prettyPrint() for x in varBind][1]}
                if "No Such Instance" in output[oid["field"]]:
                    result.update({oid["field"]: []})
                
                
                elif oid["field"] == "sysUpTime":
                    output[oid["field"]] = str(
                        datetime.timedelta(seconds=int(output["sysUpTime"]) / 100)
                    ).split(".")[0]
                    result.update(output)

                elif oid['field'] == "sysDescr":
                    if "Cisco" in output['sysDescr']:
                        result['vendor'] = "Cisco"

                    output[oid['field']] = " ".join(output['sysDescr'].split(",")[1:3])
                    result.update(output)
                else:
                    result.update(output)
        

       
        
        totalram = int(result['ciscoMemoryPoolUsed-processor']) + int(result['ciscoMemoryPoolFree-processor'])

        totalramsize = str(int(totalram / 1000000)) + "MB"

        ramusage = float(int(result['ciscoMemoryPoolUsed-processor'])) / float(totalram) *100
        result['cpmCPUTotal5minRev'] = int(result['cpmCPUTotal5minRev'])
        result['cpmCPUTotalminRev'] = int(result['cpmCPUTotalminRev'])
        result['ramusage'] = float("%.2f" % round(ramusage,2))
        result['totalramsize'] = totalramsize

        result['interfaces'] = interface_poll(community_str ,host["IP"])
        
        try:
            for interface in result['interfaces']:
                if interface['name'] == host['wan_int']:
                    result['wan_ip'] = interface['ipaddr']
                    break
                else:
                    continue
        except:
            pass


        data = {"name": host["name"], "result": result} 
    except:
        data = {"name": host["name"], "result": []}

    return data


async def do_poll(hosts, community_str,avg=None):
    """
    function for running snmp_get function Asynchronously against hosts
    """
    data = []
    coroutines = [snmp_get(host, community_str) for host in hosts]
    results = await asyncio.gather(*coroutines)
    for result in results:
        data.append(result)
    

    if avg:
        topdevices = {}
        try:
            topdevices["topramusage"] = sorted(data, key=lambda k: k['result']['ramusage'] , reverse=True)[:5]
            topdevices['topcpuusage'] = sorted(data, key=lambda k: k['result']['cpmCPUTotal5minRev'] , reverse=True)[:5]
        except:
            topdevices= {"topramusage":[] ,"topcpuusage":[] }
            
        data = topdevices


    return data


def add_ddns_url(task, dns):
    """
    create a ddns method and add URL under http method
    """
    conn = IOSXEDriver(
        host=task.host.hostname,
        auth_username=task.host.username,
        auth_password=task.host.password,
        auth_strict_key=False,
        timeout_socket=8,
        timeout_ops=10,
        timeout_transport=10,
        transport="ssh2",
    )
    conn.open()
    conn.transport.write("conf t\n")
    time.sleep(0.1)
    conn.transport.write("ip ddns update method uurnik_dns\n")
    time.sleep(0.1)
    conn.transport.write("http\n")
    time.sleep(0.1)
    conn.transport.write(f"add {os.getenv('DNSUPDATER')}")
    time.sleep(0.1)
    conn.transport.write(b"\x16")
    time.sleep(0.1)
    conn.transport.write(
        "?hostname=<h>&myip=<a>&username=uurnikhost&password=coOlAdmIn\n"
    )
    time.sleep(0.1)
    conn.close()


def resolve_host(task, dns: str):
    """
    resolving host fqdn from Uurnik DNS
    """
    try:
        my_resolver = dnsresolver.Resolver(configure=False)
        my_resolver.nameservers = [
            dns,
        ]
        answer = my_resolver.resolve(task.host.data["fqdn"], "a")
        task.host.hostname = str(answer[0])
        dbHost = Hosts.objects.get(name=task.host.name)
        dbHost.ip = task.host.hostname
        dbHost.save()
    except:
        pass



