from rest_framework import serializers
from shop.models import Plan, Order, VPNAccount

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price_irr', 'duration_days', 'data_gb']

class VPNAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VPNAccount
        fields = ['id', 'username', 'password', 'server_address', 'expires_at', 'is_active']

class OrderSerializer(serializers.ModelSerializer):
    vpn_account = VPNAccountSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'plan', 'status', 'amount_irr', 'created_at', 'vpn_account']
        read_only_fields = ['status', 'amount_irr', 'created_at', 'vpn_account']