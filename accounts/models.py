from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=255, null=True, blank=True)
    telegram_first_name = models.CharField(max_length=255, null=True, blank=True)
    telegram_last_name = models.CharField(max_length=255, null=True, blank=True)
    telegram_photo_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.telegram_username or self.username} ({self.telegram_id})"