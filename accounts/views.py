from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AdminSetPasswordForm,
    CustomUserCreationForm,
    CustomUserEditForm,
    ProfileForm,
)
from .models import CustomUser


def _is_admin(user):
    return user.is_superuser


# --- User profile (self-service) ---


def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


# --- Admin: user management ---


@user_passes_test(_is_admin)
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, "accounts/admin/user_list.html", {"users": users})


@user_passes_test(_is_admin)
def user_create(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created.')
            return redirect("accounts:user_list")
    else:
        form = CustomUserCreationForm()
    return render(
        request, "accounts/admin/user_form.html", {"form": form, "title": "Create User"}
    )


@user_passes_test(_is_admin)
def user_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = CustomUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated.')
            return redirect("accounts:user_list")
    else:
        form = CustomUserEditForm(instance=user)
    return render(
        request,
        "accounts/admin/user_form.html",
        {"form": form, "title": f"Edit User: {user.username}", "edit_user": user},
    )


@user_passes_test(_is_admin)
def user_set_password(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["password1"])
            user.save()
            messages.success(request, f'Password for "{user.username}" changed.')
            return redirect("accounts:user_list")
    else:
        form = AdminSetPasswordForm()
    return render(
        request,
        "accounts/admin/user_form.html",
        {"form": form, "title": f"Set Password: {user.username}", "edit_user": user},
    )


@user_passes_test(_is_admin)
@require_POST
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect("accounts:user_list")
    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted.')
    return redirect("accounts:user_list")
