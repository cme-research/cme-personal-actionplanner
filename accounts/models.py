from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField("email address", blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username
