from api.models import Defaults


def update_defaults_nhs(tunnel_ip, validated_data):
    """
    function for updating nhs in inventory & DB defaults when a HUB is added
    """
    if validated_data["group"] == "HUB":
        defaults = Defaults.objects.get(pk=1)

        defaults.nhs_server = defaults.nhs_server.split(",")
        defaults.nhs_server.append(tunnel_ip)
        defaults.nhs_server = ",".join(defaults.nhs_server)
        
        defaults.nhs_nbma = defaults.nhs_nbma.split(",")
        if str(validated_data["ip"]) not in defaults.nhs_nbma:
            defaults.nhs_nbma.append(str(validated_data["ip"]))
        defaults.nhs_nbma = ",".join(defaults.nhs_nbma)
        defaults.save()
