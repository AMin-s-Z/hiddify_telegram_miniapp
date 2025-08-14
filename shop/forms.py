from django import forms
from django.core.exceptions import ValidationError
from .models import Purchase

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['receipt_image']
        labels = {'receipt_image': 'فایل رسید پرداخت'}
        widgets = {'receipt_image': forms.ClearableFileInput(attrs={'class': 'form-control'})}

    def clean_receipt_image(self):
        image = self.cleaned_data.get('receipt_image', False)
        if not image: raise ValidationError("ارسال تصویر رسید الزامی است.")
        if image.size > 5 * 1024 * 1024: raise ValidationError("حجم فایل نباید بیشتر از 5 مگابایت باشد.")
        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = image.name.split('.')[-1].lower()
        if ext not in allowed_extensions: raise ValidationError(f"فرمت فایل نامعتبر است. فقط: {', '.join(allowed_extensions)}")
        return image