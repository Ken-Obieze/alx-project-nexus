
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationMemberViewSet

app_name = 'organizations'

router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')
router.register(r'members', OrganizationMemberViewSet, basename='member')

urlpatterns = [
    path('', include(router.urls)),
]