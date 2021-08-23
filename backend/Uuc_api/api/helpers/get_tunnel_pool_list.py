from netaddr import IPNetwork


def add_tunnel_pool():
    """funtion for defining a pool used in tunnel network,calculte number of host ips
    and saving it to database"""

    POOL = "172.27.0.0/16"

    host_ips = []
    for n in IPNetwork(POOL).iter_hosts():
        host_ips.append(str(n))

    return list(host_ips)


def add_static_tunnel_pool():

    POOL = "172.28.0.0/16"

    parentpools = list(IPNetwork(POOL).subnet(20))[:4]
    

    staticnetworks = []
    vendor = ""
    for i,parentpool in enumerate(parentpools,1):

        parentpool = str(parentpool)
        if i == 1:
            vendor = "fortinet"
        elif i == 2:
            vendor = "juniper"
        elif i == 3:
            vendor = "cisco"
        elif i == 4:
            vendor = "hp"
        
        networks = list(IPNetwork(parentpool).subnet(30))

        for network in networks:
            net = str(network)
            net = net.split("/")[0]

            parentpool = parentpool.split("/")[0]

            staticnetworks.append({
                "network":net,
                "vendor":vendor,
                "parentpool":parentpool
            })


        return staticnetworks
