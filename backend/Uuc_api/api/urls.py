from django.urls import path
from api.views import (
    add_Host,
    configure,
    add_remove_spoke,
    get_facts,
    tear_down,
    add_remove_hub,
    delete_host,
    ip_sla_conf,
    gather_routes,
    get_interfaces,
    copp,
    device_hardening,
    swipe_ipsec_keys,
    set_logging,
)

urlpatterns = [
    path("hosts", add_Host),
    path("hosts/delete/<str:pk>/", delete_host),
    path("configure/<int:option>/", configure),
    path("branch/<str:pk>/", add_remove_spoke),
    path("facts/", get_facts),
    path("tear-down/", tear_down),
    path("hub/<str:pk>/", add_remove_hub),
    path("ip-sla/", ip_sla_conf),
    path("routing/", gather_routes),
    path("interfaces/<str:name>/", get_interfaces),
    path("copp/", copp),
    path("device-hardening/", device_hardening),
    path("change-keys-ipsec/", swipe_ipsec_keys),
    path("logging/<str:pk>/", set_logging)
]
