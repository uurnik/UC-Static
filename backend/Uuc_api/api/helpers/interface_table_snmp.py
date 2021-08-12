from pysnmp.hlapi import *
from concurrent.futures import ThreadPoolExecutor


def build_interface_table(params) -> list:
    results = []
    data={}
    try:
        for (errorIndication,
            errorStatus,
            errorIndex,
            varBinds) in nextCmd(SnmpEngine(), 
                                CommunityData(params['pass']),
                                UdpTransportTarget((params['host'], 161), timeout=1),
                                ContextData(),                                                           
                                ObjectType(ObjectIdentity(params['OID'])),
                                lexicographicMode=False):
            
            for varBind in varBinds:
                output = [x.prettyPrint() for x in varBind][1]
                results.append(output)
        data = {params['field']:results}
    except:
        pass

    return data


def interface_poll(community_str,host):
    results = []
    oids= [
            {"field":"ifDescr","OID":"1.3.6.1.2.1.2.2.1.2","pass":community_str,"host":host},
            {"field":"ifIndex","OID":"1.3.6.1.2.1.2.2.1.1","pass":community_str,"host":host},
            {"field":"ifOperStatus","OID":"1.3.6.1.2.1.2.2.1.8","pass":community_str,"host":host},
            {"field":"ipAdEntIfIndex","OID":"1.3.6.1.2.1.4.20.1.2","pass":community_str,"host":host},
            {"field":"ipAdEntAddr","OID":"1.3.6.1.2.1.4.20.1.1","pass":community_str,"host":host},
            {"field":"ifAdminStatus","OID":"1.3.6.1.2.1.2.2.1.7","pass":community_str,"host":host}

    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        execute=executor.map(build_interface_table ,oids)
        data = list(execute)
        index_desc = list(zip(data[0]["ifDescr"] , data[2]["ifOperStatus"],data[1]["ifIndex"] , data[5]['ifAdminStatus']))
        index_ip =  list(zip(data[3]["ipAdEntIfIndex"] , data[4]["ipAdEntAddr"]))

        for interface in index_desc:
            interface_result= {"name":interface[0],"status":interface[1] ,  "adminstatus":interface[3]}
            for addressed_int in index_ip:
                if interface[2] == addressed_int[0]:
                    interface_result["ipaddr"] = addressed_int[1]
            
            if not interface_result.get("ipaddr"):
                interface_result['ipaddr'] = "unassigned"

            results.append(interface_result)

        return results





# Get all interface names > 1.3.6.1.2.1.2.2.1.2
# Get Ip addresses on interfaces > 1.3.6.1.2.1.4.20.1.1
# Get Interface Index for IP addressed Interfaces > ipAdEntIfIndex (1.3.6.1.2.1.4.20.1.2)


# Get interface Operational Status > 1.3.6.1.2.1.2.2.1.8
#2 : down
#3 : testing
#4 : unknown
#5 : dormant
#6 : notPresent
#7 : lowerLayerDown