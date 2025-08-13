from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    telegram_first_name = models.CharField(max_length=100, null=True, blank=True)
    telegram_last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.telegram_username or self.username}"