from django.db import models
from django.contrib.auth.models import User

class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()  # e.g., 30 days

    def __str__(self):
        return self.name

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    vpn_config = models.TextField(null=True, blank=True)  # Store VPN config here after creation

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"