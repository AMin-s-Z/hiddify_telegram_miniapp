import secrets
from datetime import datetime, timedelta
from django.conf import settings
from .models import Order, VPNAccount


def create_vpn_account_for_order(order: Order) -> VPNAccount:
    username = f"u{order.user.id}{secrets.token_hex(2)}"
    password = secrets.token_urlsafe(10)
    server_address = getattr(settings, "VPN_SERVER_ADDRESS", "vpn.example.com")
    expires_at = datetime.utcnow() + timedelta(days=order.plan.duration_days)
    account = VPNAccount.objects.create(
        user=order.user,
        plan=order.plan,
        username=username,
        password=password,
        server_address=server_address,
        expires_at=expires_at,
        order=order,
    )
    return account 