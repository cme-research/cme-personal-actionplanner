import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="adminpass123", email="admin@example.com"
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular", password="userpass123", email="user@example.com"
    )


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.login(username="admin", password="adminpass123")
    return c


@pytest.fixture
def user_client(regular_user):
    c = Client()
    c.login(username="regular", password="userpass123")
    return c


class TestProfile:
    def test_profile_requires_login(self, db):
        c = Client()
        response = c.get("/accounts/profile/")
        assert response.status_code == 302

    def test_profile_page_loads(self, user_client):
        response = user_client.get("/accounts/profile/")
        assert response.status_code == 200

    def test_change_email(self, user_client, regular_user):
        response = user_client.post(
            "/accounts/profile/", {"email": "newemail@example.com"}
        )
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.email == "newemail@example.com"


class TestAdminUserList:
    def test_requires_superuser(self, user_client):
        response = user_client.get("/accounts/admin/users/")
        assert response.status_code == 302

    def test_admin_can_access(self, admin_client):
        response = admin_client.get("/accounts/admin/users/")
        assert response.status_code == 200


class TestAdminUserCreate:
    def test_create_user(self, admin_client):
        response = admin_client.post(
            "/accounts/admin/users/create/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "strongpass987!",
                "password2": "strongpass987!",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    def test_regular_user_cannot_create(self, user_client):
        response = user_client.post(
            "/accounts/admin/users/create/",
            {
                "username": "hacker",
                "password1": "pass123456!",
                "password2": "pass123456!",
            },
        )
        assert response.status_code == 302  # redirects to login
        assert not User.objects.filter(username="hacker").exists()


class TestAdminUserEdit:
    def test_edit_user(self, admin_client, regular_user):
        response = admin_client.post(
            f"/accounts/admin/users/{regular_user.pk}/edit/",
            {
                "username": "regular",
                "email": "changed@example.com",
                "is_active": True,
            },
        )
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.email == "changed@example.com"


class TestAdminUserDelete:
    def test_delete_user(self, admin_client, regular_user):
        response = admin_client.post(
            f"/accounts/admin/users/{regular_user.pk}/delete/"
        )
        assert response.status_code == 302
        assert not User.objects.filter(username="regular").exists()

    def test_cannot_delete_self(self, admin_client, admin_user):
        response = admin_client.post(
            f"/accounts/admin/users/{admin_user.pk}/delete/"
        )
        assert response.status_code == 302
        assert User.objects.filter(username="admin").exists()


class TestAdminSetPassword:
    def test_set_password(self, admin_client, regular_user):
        response = admin_client.post(
            f"/accounts/admin/users/{regular_user.pk}/password/",
            {"password1": "newstrongpass!", "password2": "newstrongpass!"},
        )
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.check_password("newstrongpass!")

    def test_mismatched_passwords(self, admin_client, regular_user):
        response = admin_client.post(
            f"/accounts/admin/users/{regular_user.pk}/password/",
            {"password1": "pass1", "password2": "pass2"},
        )
        assert response.status_code == 200  # re-renders form with errors
