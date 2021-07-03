from rest_framework import serializers
from .models import Hosts, Defaults, Account
from ipaddress import ip_address
import re


class HostsSerializer(serializers.ModelSerializer):
    ip = serializers.IPAddressField(required=True)
    name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
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
