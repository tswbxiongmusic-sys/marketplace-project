from django import forms

from .models import Order, ShippingMethod


class ShippingMethodChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, shipping_method):
        estimate = f" · {shipping_method.estimated_delivery}" if shipping_method.estimated_delivery else ""
        return f"{shipping_method.name} — ₭{shipping_method.fee:,.0f}{estimate}"


class CheckoutForm(forms.Form):
    recipient_name = forms.CharField(max_length=150, label="ຊື່ຜູ້ຮັບ")
    phone = forms.CharField(max_length=20, label="ເບີໂທ")
    shipping_address = forms.CharField(
        label="ທີ່ຢູ່ຈັດສົ່ງ", widget=forms.Textarea(attrs={"rows": 3})
    )
    shipping_method = ShippingMethodChoiceField(
        label="ວິທີຈັດສົ່ງ",
        queryset=ShippingMethod.objects.none(),
        empty_label=None,
        widget=forms.RadioSelect,
        help_text="ເລືອກວິທີຈັດສົ່ງທີ່ເໝາະກັບທ່ານ.",
    )
    payment_method = forms.ChoiceField(
        label="ວິທີຊຳລະ", choices=Order.PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect
    )
    payment_receipt = forms.ImageField(required=False, label="ຫຼັກຖານການໂອນເງິນ")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shipping_methods = ShippingMethod.objects.filter(is_active=True)
        self.fields["shipping_method"].queryset = shipping_methods

        for field_name in ("recipient_name", "phone", "shipping_address", "payment_receipt"):
            css_class = "form-control"
            self.fields[field_name].widget.attrs["class"] = css_class

        self.fields["shipping_method"].widget.attrs["class"] = "form-check-input"
        self.fields["payment_method"].widget.attrs["class"] = "form-check-input"

        if not self.is_bound and not self.initial.get("shipping_method"):
            default_method = shipping_methods.first()
            if default_method:
                self.initial["shipping_method"] = default_method.pk

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_method") in {"bank_transfer", "qr_payment"} and not cleaned.get("payment_receipt"):
            self.add_error("payment_receipt", "ກະລຸນາອັບໂຫຼດຫຼັກຖານການໂອນເງິນ.")
        return cleaned
