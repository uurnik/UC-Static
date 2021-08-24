import socket
from api.helpers.inventory_builder import inventory
from api.models import Defaults , Hosts , StaticTunnelNet


def dns_conn_check(dns):
    result = True
    dns_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dns_socket.settimeout(5)
    result_of_check = dns_socket.connect_ex((dns, 53))
    if result_of_check == 0:
        pass
    else:
        result = False
    
    return result




class PreConfig():

    def __init__(self):
        self.headend_vendor = None
        self.vendor_list = []


    def get_vendors(self):
        self.headend_vendor = Hosts.objects.filter(group='HUB')[0].vendor
        self.vendor_list.append(self.headend_vendor)
        
        try:
            other_vendors = Hosts.objects.exclude(vendor="Cisco")
            for device in other_vendors:
                self.vendor_list.append(device.vendor)
        except:
            pass

        vendor_str = ",".join(self.vendor_list)

        dbDefaults = Defaults.objects.get(pk=1)
        dbDefaults.headend_vendor = self.headend_vendor
        dbDefaults.vendor_list = vendor_str
        dbDefaults.save()


    def assign_static_tunnels(self) -> tuple:
        self.get_vendors()

        static_sites=[]
        if self.headend_vendor == "Cisco" and len(self.vendor_list) > 1:
            tunnel_id=414
            other_vendors_devices = Hosts.objects.exclude(vendor="Cisco")

            for device in other_vendors_devices:
                dbHost = Hosts.objects.get(name=device.name)
                static_tunnel = StaticTunnelNet.objects.filter(vendor=device.vendor.lower(), used=False)[0]
                dbHost.static_tunnel_network = static_tunnel.network
                static_tunnel.used=True
                static_tunnel.save()
                dbHost.save()

                tunnel_id += 1
                
                remote_tunnel_ip = static_tunnel.network.split(".")[3]
                remote_temp = static_tunnel.network.split(".")[:3]
                remote_temp.append(str(int(remote_tunnel_ip) + 2))
                remote_tunnel_ip = ".".join(remote_temp)

                network_tunnel = static_tunnel.network.split(".")[3]
                temp = static_tunnel.network.split(".")[:3]
                temp.append(str(int(network_tunnel) + 1))
                tunnel_ip = ".".join(temp)


                static_sites.append({
                    "site_name":device.name,
                    "tunnel_network":static_tunnel.network,
                    "site_public_ip":device.ip,
                    "tunnel_id":tunnel_id,
                    "tunnel_ip":tunnel_ip,
                    "remote_tunnel_ip":remote_tunnel_ip
                })
        
        return (self.headend_vendor , static_sites)