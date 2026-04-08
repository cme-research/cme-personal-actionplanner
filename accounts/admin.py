from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "is_active", "is_staff", "is_superuser"]
    list_filter = ["is_active", "is_staff", "is_superuser"]
