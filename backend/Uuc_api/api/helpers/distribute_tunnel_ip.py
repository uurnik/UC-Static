from api.models import Defaults


def update_defaults_nhs(tunnel_ip, serializer):
    """
    function for updating nhs in inventory & DB defaults when a HUB is added

        :params:
            tunnel_ip: tunnel IP of the hub being added

            serializer: host serializer object
    """
    if serializer.validated_data["group"] == "HUB":
        defaults = Defaults.objects.get(pk=1)

        defaults.nhs_server = defaults.nhs_server.split(",")
        defaults.nhs_server.append(tunnel_ip)
        defaults.nhs_server = ",".join(defaults.nhs_server)

        defaults.nhs_nbma = defaults.nhs_nbma.split(",")
        if str(serializer.validated_data["ip"]) not in defaults.nhs_nbma:
            defaults.nhs_nbma.append(str(serializer.validated_data["ip"]))
        defaults.nhs_nbma = ",".join(defaults.nhs_nbma)
        defaults.save()
