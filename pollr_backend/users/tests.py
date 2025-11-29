from django.test import TestCase
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import UserRole, UserStatus

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def regular_user(db):
    """Fixture for regular user."""
    return User.objects.create_user(
        email='user@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe',
        role=UserRole.USER
    )


@pytest.fixture
def super_admin(db):
    """Fixture for super admin user."""
    user = User.objects.filter(email='admin@example.com').first()
    if user:
        return user
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def org_admin(db):
    """Fixture for organization admin user."""
    return User.objects.create_user(
        email='orgadmin@example.com',
        password='orgpass123',
        first_name='Org',
        last_name='Admin',
        role=UserRole.ORG_ADMIN
    )


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration."""
    
    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = reverse('users:user-list')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@example.com').exists()
        assert 'password' not in response.data
    
    def test_register_user_password_mismatch(self, api_client):
        """Test registration with mismatched passwords."""
        url = reverse('users:user-list')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_register_user_duplicate_email(self, api_client, regular_user):
        """Test registration with existing email."""
        url = reverse('users:user-list')
        data = {
            'email': regular_user.email,
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data


@pytest.mark.django_db
class TestUserAuthentication:
    """Test user authentication."""
    
    def test_login_success(self, api_client, regular_user):
        """Test successful login."""
        url = reverse('users:token_obtain_pair')
        data = {
            'email': 'user@example.com',
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self, api_client, regular_user):
        """Test login with invalid credentials."""
        url = reverse('users:token_obtain_pair')
        data = {
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, api_client, regular_user):
        """Test token refresh."""
        # First, login to get tokens
        login_url = reverse('users:token_obtain_pair')
        login_data = {
            'email': 'user@example.com',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Then refresh the token
        refresh_url = reverse('users:token_refresh')
        refresh_data = {'refresh': refresh_token}
        
        response = api_client.post(refresh_url, refresh_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile operations."""
    
    def test_get_own_profile(self, api_client, regular_user):
        """Test getting own profile."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('users:user-me')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == regular_user.email
        assert response.data['full_name'] == 'John Doe'
    
    def test_update_own_profile(self, api_client, regular_user):
        """Test updating own profile."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('users:user-detail', kwargs={'pk': regular_user.pk})
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Jane'
        assert regular_user.last_name == 'Smith'
    
    def test_cannot_update_other_profile(self, api_client, regular_user, super_admin):
        """Test that users cannot update other users' profiles."""
        api_client.force_authenticate(user=regular_user)
        url = f"/api/v1/users/{super_admin.id}/"
        response = api_client.patch(url, {"first_name": "NewName"}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPasswordChange:
    """Test password change functionality."""
    
    def test_change_password_success(self, api_client, regular_user):
        """Test successful password change."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('users:user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.check_password('newpass456')
    
    def test_change_password_wrong_old(self, api_client, regular_user):
        """Test password change with wrong old password."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('users:user-change-password')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserAdministration:
    """Test user administration by super admin."""
    
    def test_super_admin_list_users(self, api_client, super_admin, regular_user):
        """Test super admin can list all users."""
        api_client.force_authenticate(user=super_admin)
        url = reverse('users:user-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
    
    def test_regular_user_cannot_list_users(self, api_client, regular_user):
        """Test regular user cannot list all users."""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v1/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_suspend_user(self, api_client, super_admin, regular_user):
        """Test suspending a user."""
        api_client.force_authenticate(user=super_admin)
        url = reverse('users:user-suspend', kwargs={'pk': regular_user.pk})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.status == UserStatus.SUSPENDED
    
    def test_activate_user(self, api_client, super_admin, regular_user):
        """Test activating a suspended user."""
        regular_user.suspend()
        api_client.force_authenticate(user=super_admin)
        url = reverse('users:user-activate', kwargs={'pk': regular_user.pk})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.status == UserStatus.ACTIVE
    
    def test_get_user_statistics(self, api_client, super_admin, regular_user, org_admin):
        """Test getting user statistics."""
        api_client.force_authenticate(user=super_admin)
        url = reverse('users:user-statistics')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_users' in response.data
        assert 'active_users' in response.data
        assert response.data['total_users'] >= 3