from rest_framework.routers import DefaultRouter
from monitoring.views import ConnectTest ,AppOverview ,SNMPView ,TopologyView



app_name = "monitoring"

router = DefaultRouter()
router.register(r'testconn', ConnectTest, basename='testconn')
router.register(r'summary', AppOverview, basename='summary')
router.register(r'snmp', SNMPView, basename='snmp')
router.register(r'topology', TopologyView, basename='topology')



urlpatterns = router.urls
