from rest_framework import serializers
from .models import Hosts, Defaults,TunnelPool,CacheTable
from .helpers.distribute_tunnel_ip import update_defaults_nhs
import re
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.http import JsonResponse

from .helpers.inventory_builder import inventory
from .nornir_stuff.configure_nodes import change_ipsec_keys ,resolve_host


class HostsSerializer(serializers.ModelSerializer):
    ip = serializers.IPAddressField(required=True)
    name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    port = serializers.IntegerField(required=False)
    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
    )
    group = serializers.CharField(required=True)

    class Meta:
        model = Hosts
        fields = [
            "ip",
            "name",
            "username",
            "password",
            "port",
            "platform",
            "group",
            "is_configured",
            "wan_int",
            "wan_subnet",
            "tunnel_ip",
            "loop_back",
            "next_hop",
            "vendor",
            "model",
            "ram_size",
            "os_version",
            "serial_no",
            "dev_name",
            "interfaces",
            "fhrp",
            "fhrp_interface",
            "primary_router",
            "virtual_ip",
        ]

    def validate_name(self, value):
        """
        validate 'name' field
        """
        if len(value) > 12:
            raise serializers.ValidationError("must be under 12 characters")

        p = re.findall("[,*/+=;:]", value)
        if len(p) != 0:
            raise serializers.ValidationError("must not include ',*/+=;:'")

        if " " in value:
            raise serializers.ValidationError("must not include any spaces")

        return value
    

    def save(self):
        """
        function to add Hosts in the Hosts table, it will assign the tunnel IP to the host being added,
        first looking for tunnel IP in the CacheTable, if not found,
        An unused IP will assigned from the TunnelPool Table,
        if host being added is a HUB then its NBMA and tunnel IP will also be added to Defaults Table
        """
        have_ip = False
            # checking if tunnel ip for the host exists in the cache table , if found that ip is assigned as tunnel ip
            # Checked on the bases of the WAN ip of the host
        for cached_ip in CacheTable.objects.all():
            if cached_ip.device_ip == self.validated_data["ip"]:
                self.validated_data["tunnel_ip"] = cached_ip.ip
                cached_ip.save()
                try:
                    Hosts.objects.create(**self.validated_data)
                except IntegrityError:
                    return JsonResponse(
                        {"detail": "Host with this IP/name already exists"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                update_defaults_nhs(cached_ip.ip, self.validated_data)
                have_ip = True
                break
            else:
                continue

        # Assign tunnel IP from TunnelPool if iIP not found in Cache Table, Assigned IP is the marked as used
        if have_ip is False:
            tunnel_ip = TunnelPool.objects.filter(is_used=False)[0]
            self.validated_data["tunnel_ip"] = tunnel_ip.ip
            tunnel_ip.is_used = True
            insert_cache = CacheTable(
                ip=tunnel_ip.ip,
                in_use=True,
                device_ip=self.validated_data["ip"],
            )
            insert_cache.save()
            tunnel_ip.save()
            try:
                Hosts.objects.create(**self.validated_data)
            except IntegrityError:
                return JsonResponse(
                    {"detail": "Host with this IP/name already exists"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            update_defaults_nhs(tunnel_ip.ip, self.validated_data)
            have_ip = True
        else:
            pass

        return Response(status=status.HTTP_201_CREATED)





class DefaultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Defaults
        fields = [
            "tunnel_int",
            "asn",
            "policy_num",
            "ipsec_key",
            "trans_name",
            "profile_name",
            "nhs_server",
            "nhs_nbma",
            "access_type",
            "ip_sla_process",
            "track_ip",
            "is_sla_configured",
        ]


    def change_ipsec_key(self ,keys):
        nr = inventory()
        # query dns and update inventory
        dns = Defaults.objects.get(pk=1).dns
        if dns != None:
            nr.run(task=resolve_host, dns=dns)
        #####################################

        new_key = keys["new_key"]
        if nr.inventory.defaults.data["ipsec_key"] != keys["old_key"]:
            return JsonResponse(
                {"error": "Invalid Key"}, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        if len(new_key) < 8 or len(new_key) > 16:
            return JsonResponse(
                {"error": "Key must be of 8-16 characters"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        if (
            any(x.isupper() for x in new_key)
            and any(x.islower() for x in new_key)
            and any(x.isdigit() for x in new_key)
            and any(x.isalnum() for x in new_key)
        ):
            import string

            invalidChars = set(string.punctuation.replace("_", ""))
            if any(char in invalidChars for char in new_key):
                pass
            else:
                return JsonResponse(
                    {
                        "error": "Must include 1 upper case letter,a digit and a special character"
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
        else:
            return JsonResponse(
                {
                    "error": "Must include 1 upper case letter,a digit and a special character"
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        result = nr.run(task=change_ipsec_keys, new_key=new_key)

        # Save new key in DB
        dbDefaults = Defaults.objects.get(pk=1)
        dbDefaults.ipsec_key = new_key
        dbDefaults.save()

        data = []
        for host in nr.inventory.hosts.keys():
            data.append(
                {
                    "name": nr.inventory.hosts[host].name,
                    "changed": result[host].changed,
                    "failed": result[host].failed,
                }
            )

        return JsonResponse(data, safe=False)