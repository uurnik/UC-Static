from netaddr import IPNetwork


def add_tunnel_pool():
    """funtion for defining a pool used in tunnel network,calculte number of host ips
    and saving it to database"""

    POOL = "172.27.0.0/16"

    host_ips = []
    for n in IPNetwork(POOL).iter_hosts():
        host_ips.append(str(n))

    return list(host_ips)
