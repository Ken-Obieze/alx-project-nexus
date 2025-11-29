from rest_framework import routers
from .views.organization import OrganizationViewSet

router = routers.DefaultRouter()
router.register("organizations", OrganizationViewSet)

urlpatterns = router.urls