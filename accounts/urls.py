from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Self-service
    path("profile/", views.profile, name="profile"),
    # Admin: user management
    path("admin/users/", views.user_list, name="user_list"),
    path("admin/users/create/", views.user_create, name="user_create"),
    path("admin/users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("admin/users/<int:pk>/password/", views.user_set_password, name="user_set_password"),
    path("admin/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
