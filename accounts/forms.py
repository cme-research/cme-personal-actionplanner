from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"


class CustomUserEditForm(forms.ModelForm):
    """Admin form for editing an existing user (no password fields)."""

    class Meta:
        model = CustomUser
        fields = ("username", "email", "is_active", "is_staff", "is_superuser")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AdminSetPasswordForm(forms.Form):
    """Admin form for resetting a user's password."""

    password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileForm(forms.ModelForm):
    """User self-service form for changing email."""

    class Meta:
        model = CustomUser
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
