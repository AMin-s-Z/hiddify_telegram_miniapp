from rest_framework import serializers
from shop.models import Plan, Order, VPNAccount

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price_irr',
            'duration_days', 'data_gb', 'is_active'
        ]

class VPNAccountSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='order.plan.name', read_only=True)

    class Meta:
        model = VPNAccount
        fields = [
            'id', 'username', 'password', 'server_address',
            'expires_at', 'is_active', 'created_at', 'plan_name'
        ]

class OrderSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    vpn_account = VPNAccountSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'plan', 'status', 'status_display', 'amount_irr',
            'admin_note', 'created_at', 'updated_at', 'vpn_account'
        ]
        read_only_fields = [
            'status', 'amount_irr', 'created_at', 'updated_at', 'admin_note'
        ]