from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model('accounts', 'Plan')
    items = [
        {"name": "پلن ۲۰ گیگابایت", "description": "حجم: ۲۰ گیگ", "price_irr": 6500000, "duration_days": 30, "data_gb": 20, "order_index": 1},
        {"name": "پلن ۳۰ گیگابایت", "description": "حجم: ۳۰ گیگ", "price_irr": 8500000, "duration_days": 30, "data_gb": 30, "order_index": 2},
        {"name": "پلن ۵۰ گیگابایت (پیشنهاد ویژه)", "description": "حجم: ۵۰ گیگ", "price_irr": 12000000, "duration_days": 30, "data_gb": 50, "order_index": 3},
        {"name": "پلن ۷۰ گیگابایت", "description": "حجم: ۷۰ گیگ", "price_irr": 15000000, "duration_days": 30, "data_gb": 70, "order_index": 4},
        {"name": "پلن ۱۰۰ گیگابایت (به‌صرفه‌ترین)", "description": "حجم: ۱۰۰ گیگ", "price_irr": 19000000, "duration_days": 30, "data_gb": 100, "order_index": 5},
    ]
    for i in items:
        Plan.objects.update_or_create(name=i["name"], defaults=i)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model('accounts', 'Plan')
    names = [
        "پلن ۲۰ گیگابایت",
        "پلن ۳۰ گیگابایت",
        "پلن ۵۰ گیگابایت (پیشنهاد ویژه)",
        "پلن ۷۰ گیگابایت",
        "پلن ۱۰۰ گیگابایت (به‌صرفه‌ترین)",
    ]
    Plan.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_plan_order_vpnaccount'),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ] 