from django.conf import settings

def bank_card_number(request):
    return {'bank_card_number': settings.BANK_CARD_NUMBER}