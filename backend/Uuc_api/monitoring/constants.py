COMMUNITY_STR="uurnik123"



FORTINET_OIDS = {
    "interface_oids":[
            {"field":"ifDescr","OID":"1.3.6.1.2.1.31.1.1.1.1"},
            {"field":"ifIndex","OID":"1.3.6.1.2.1.2.2.1.1"},
            {"field":"ifOperStatus","OID":"1.3.6.1.2.1.2.2.1.8"},
            {"field":"ipAdEntIfIndex","OID":"1.3.6.1.2.1.4.20.1.2"},
            {"field":"ipAdEntAddr","OID":"1.3.6.1.2.1.4.20.1.1"},
            {"field":"ifAdminStatus","OID":"1.3.6.1.2.1.2.2.1.7"},
            {"field":"ifOutOctets","OID":"1.3.6.1.2.1.2.2.1.16"},
            {"field":"ifInOctets","OID":"1.3.6.1.2.1.2.2.1.10"},
            {"field":"ifInErrors","OID":"1.3.6.1.2.1.2.2.1.14"},
            {"field":"ifOutErrors","OID":"1.3.6.1.2.1.2.2.1.20"},
            {"field":"ifPhysAddress","OID":"1.3.6.1.2.1.2.2.1.6"},
    ],
    'sys_oids':[
           {
                "field": "sysDescr",
                "OID": "1.3.6.1.2.1.47.1.1.1.1.10",
            },
            
            {
                "field": "usedmemory",
                "OID": "1.3.6.1.4.1.12356.101.4.1.4",
            },
            {
                "field": "totalmemory",
                "OID": "1.3.6.1.4.1.12356.101.4.1.5",
            },
            {"field": "cpuusage", "OID": "1.3.6.1.4.1.12356.101.4.1.3"},
            {"field": "sysUpTime", "OID": "1.3.6.1.2.1.1.3"},
            {"field": "fqdn","OID":"1.3.6.1.2.1.1.5"},
            {"field": "chassisid","OID":"1.3.6.1.4.1.12356.100.1.1.1"}
    ]
}


CISCO_OIDS = {
    "interface_oids": [
                {"field":"ifDescr","OID":"1.3.6.1.2.1.2.2.1.2"},
                {"field":"ifIndex","OID":"1.3.6.1.2.1.2.2.1.1"},
                {"field":"ifOperStatus","OID":"1.3.6.1.2.1.2.2.1.8"},
                {"field":"ipAdEntIfIndex","OID":"1.3.6.1.2.1.4.20.1.2"},
                {"field":"ipAdEntAddr","OID":"1.3.6.1.2.1.4.20.1.1"},
                {"field":"ifAdminStatus","OID":"1.3.6.1.2.1.2.2.1.7"},
                {"field":"ifOutOctets","OID":"1.3.6.1.2.1.2.2.1.16"},
                {"field":"ifInOctets","OID":"1.3.6.1.2.1.2.2.1.10"},
                {"field":"ifInErrors","OID":"1.3.6.1.2.1.2.2.1.14"},
                {"field":"ifOutErrors","OID":"1.3.6.1.2.1.2.2.1.20"},
                {"field":"ifPhysAddress","OID":"1.3.6.1.2.1.2.2.1.6"},
    ],
    "sys_oids": [

                {
                    "field": "sysDescr",
                    "OID": "1.3.6.1.2.1.1.1",
                },
                {
                    "field": "ciscoMemoryPoolUsed-processor",
                    "OID": "1.3.6.1.4.1.9.9.48.1.1.1.5",
                },
                {
                    "field": "ciscoMemoryPoolFree-processor",
                    "OID": "1.3.6.1.4.1.9.9.48.1.1.1.6",
                },
                # {"field": "cpmCPUTotal5minRev", "OID": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"},
                {"field": "cpuusage", "OID": "1.3.6.1.4.1.9.9.109.1.1.1.1.7"},
                {"field": "sysUpTime", "OID": "1.3.6.1.2.1.1.3"},
                {"field": "fqdn","OID":"1.3.6.1.2.1.1.5"},
                {"field": "chassisid","OID":"1.3.6.1.4.1.9.3.6.3"}
    ]
                
                
}