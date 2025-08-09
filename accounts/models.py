from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram_profile")
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_username = models.CharField(max_length=255, blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    language_code = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.telegram_id})"
