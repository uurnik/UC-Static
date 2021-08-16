from rest_framework import viewsets, permissions
import asyncio
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.helpers.inventory_builder import inventory
from api.helpers.misc import resolve_host
from nornir.core.filter import F
from .utils import check_conn , SNMPManager
from api.models import Defaults
from .utils import test_ssh_conn , do_ping ,TopologyBuilder
from nornir.core.deserializer.inventory import Inventory



class ConnectTest(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def ping_inventory(self,request):
        nr = inventory()

        # query dns and update inventory
        dns = Defaults.objects.get(pk=1).dns
        if dns != None:
            nr.run(task=resolve_host, dns=dns)
        #####################################

        return Response(do_ping(nr))
        

    @action(detail=False, methods=["get"])
    def check_alive(self , request):
        nr = inventory()
        dns = Defaults.objects.get(pk=1).dns

        if request.query_params.get("name"):
            name = request.query_params.get("name")
            device = nr.filter(F(name=name))
            device.run(task=resolve_host, dns=dns)
            result = device.run(task=test_ssh_conn)
            data = {"name": name, "alive": result[name][0].result}
        else:
            # query dns and update inventory
            if dns != None:
                nr.run(task=resolve_host, dns=dns)
            #####################################
            result = nr.run(task=test_ssh_conn)
            data = []
            for h in nr.inventory.hosts.keys():
                data.append(
                    {"name": nr.inventory.hosts[h].name, "alive": result[h][0].result}
                )

        return Response(data)


    def list(self , request):
        nr = inventory()
        data={}
        dev_name = request.query_params.get("name")
        dest = request.query_params.get("dest")
        nr = inventory()
        device = nr.filter(F(dev_name=dev_name))

        result = device.run(task=check_conn , dest=dest)

        for host in device.inventory.hosts.keys():
            data['result'] = result[host][0].result

        return Response(data)


class AppOverview(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self ,request):
        nr = inventory()
        data = {}

        managed_inv = nr.filter(F(is_configured=True))
        data['managed'] = len(managed_inv.inventory.hosts.keys())

        unmanaged = nr.filter(F(is_configured=False))
        data['unmanaged'] = len(unmanaged.inventory.hosts.keys())

        data['total'] = len(nr.inventory.hosts.keys())

        return Response(data)


    @action(detail=False, methods=["get"])
    def get_access_type(self , request):
        dbDefaults = Defaults.objects.get(pk=1)
        access_type_number = dbDefaults.access_type
        device_hardening = dbDefaults.is_device_hardening_configured
        copp_configured = dbDefaults.is_copp_configured

        if access_type_number == 1:
            access_type = "Private WAN only"
        elif access_type_number == 2:
            access_type = "Private WAN + Direct Internet Access"
        elif access_type_number == 3:
            access_type = "Private WAN + Direct Internet Access + Addons"
        else:
            access_type = None
        


        return Response({"access_type": access_type,"copp":copp_configured,"device_hardening":device_hardening})


    @action(detail=False, methods=["get"])
    def inventory(self,request):                    # TODO Temporary view
        nr = inventory()
        a_inventory = Inventory.serialize(nr.inventory).dict()
        return Response({"inventory": a_inventory})



class SNMPView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


    def list(self ,request):
        nr = inventory()

        # query dns and update inventory
        dns = Defaults.objects.get(pk=1).dns
        if dns != None:
            nr.run(task=resolve_host, dns=dns)
        #####################################

        hosts = []
        avg=None
        if request.query_params.get("avg"):
            avg = True

        if request.query_params.get("name"):
            name = request.query_params.get("name")
            device = nr.filter(F(name=name))
            for host in device.inventory.hosts.keys():
                try:
                    hosts.append(
                    {
                        "name": nr.inventory.hosts[host].name,
                        "IP": nr.inventory.hosts[host].hostname,
                        "int_index": nr.inventory.hosts[host].data["interface_index"],
                        "wan_int": nr.inventory.hosts[host].data["wan_int"],
                    }
                )
                except:
                    pass
        else:
            for host in nr.inventory.hosts.keys():
                try:
                    hosts.append(
                        {
                            "name": nr.inventory.hosts[host].name,
                            "IP": nr.inventory.hosts[host].hostname,
                            "int_index": nr.inventory.hosts[host].data["interface_index"],
                            "wan_int": nr.inventory.hosts[host].data["wan_int"],

                        }
                    )
                except:
                    pass


        output = SNMPManager().get_data(hosts ,avg=avg)

        return Response(output)







class TopologyView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_neighbors(self , request):
        data = TopologyBuilder().build_topology()
        return Response(data)
