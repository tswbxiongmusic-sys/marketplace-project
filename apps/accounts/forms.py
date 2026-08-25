from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.products.models import Category

from .models import SellerApplication, User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control"}
        ),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "phone",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "username": "ຊື່ຜູ້ໃຊ້", "email": "ອີເມວ", "phone": "ເບີໂທ",
            "password1": "ລະຫັດຜ່ານ", "password2": "ຢືນຢັນລະຫັດຜ່ານ",
        }
        for field, label in labels.items():
            self.fields[field].label = label


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "avatar",
            "address",
        )
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "avatar": forms.FileInput(
                attrs={"class": "form-control"}
            ),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

        labels = {
            "first_name": "ຊື່", "last_name": "ນາມສະກຸນ", "email": "ອີເມວ",
            "phone": "ເບີໂທ", "avatar": "ຮູບໂປຣໄຟລ໌", "address": "ທີ່ຢູ່",
        }


class SellerPaymentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "bank_name",
            "bank_account_name",
            "bank_account_number",
            "payment_qr",
        )
        widgets = {
            "bank_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ເຊັ່ນ: BCEL, LDB, ..."}
            ),
            "bank_account_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "bank_account_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "payment_qr": forms.FileInput(
                attrs={"class": "form-control"}
            ),
        }
        labels = {
            "bank_name": "ຊື່ທະນາຄານ",
            "bank_account_name": "ຊື່ບັນຊີ",
            "bank_account_number": "ເລກບັນຊີ",
            "payment_qr": "ຮູບ QR ຮັບເງິນ",
        }


class SellerAccountForm(UserCreationForm):
    """Only used for a visitor who does not have a site account yet."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "username": "ຊື່ຜູ້ໃຊ້ (ສຳລັບເຂົ້າລະບົບ)",
            "password1": "ລະຫັດຜ່ານ",
            "password2": "ຢືນຢັນລະຫັດຜ່ານ",
        }
        for field, label in labels.items():
            self.fields[field].label = label
            self.fields[field].widget.attrs["class"] = "form-control"


class SellerStoreProfileForm(forms.ModelForm):
    """Owner + store branding info, saved directly onto the User model."""

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "email", "phone", "address",
            "store_name", "store_logo", "store_category", "store_description",
            "facebook_url", "tiktok_url", "website_url",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "store_name": forms.TextInput(attrs={"class": "form-control"}),
            "store_logo": forms.FileInput(attrs={"class": "form-control"}),
            "store_category": forms.Select(attrs={"class": "form-select"}),
            "store_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://facebook.com/..."}),
            "tiktok_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://tiktok.com/@..."}),
            "website_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }
        labels = {
            "first_name": "ຊື່", "last_name": "ນາມສະກຸນ", "email": "ອີເມວ",
            "phone": "ເບີໂທ", "address": "ທີ່ຢູ່",
            "store_name": "ຊື່ຮ້ານ", "store_logo": "ໂລໂກ້ຮ້ານ",
            "store_category": "ປະເພດສິນຄ້າ", "store_description": "ຄຳອະທິບາຍຮ້ານ",
            "facebook_url": "Facebook Page", "tiktok_url": "TikTok", "website_url": "Website ຂອງຮ້ານ",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["store_category"].queryset = Category.objects.order_by("name")
        self.fields["store_category"].required = False
        for optional in ("address", "store_logo", "store_description", "facebook_url", "tiktok_url", "website_url"):
            self.fields[optional].required = False


class SellerApplicationForm(forms.ModelForm):
    class Meta:
        model = SellerApplication
        fields = (
            "business_type",
            "business_registration_number",
            "verification_document",
            "agreed_seller_agreement",
            "agreed_privacy_policy",
            "agreed_seller_rules",
        )
        widgets = {
            "business_type": forms.Select(attrs={"class": "form-select"}),
            "business_registration_number": forms.TextInput(attrs={"class": "form-control"}),
            "verification_document": forms.FileInput(attrs={"class": "form-control"}),
            "agreed_seller_agreement": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "agreed_privacy_policy": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "agreed_seller_rules": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "business_type": "ປະເພດທຸລະກິດ",
            "business_registration_number": "ເລກຈົດທະບຽນທຸລະກິດ (ຖ້າມີ)",
            "verification_document": "ຮູບ/ເອກະສານຢືນຢັນ",
            "agreed_seller_agreement": "ຂ້ອຍອ່ານ ແລະຍອມຮັບ Seller Agreement",
            "agreed_privacy_policy": "ຂ້ອຍອ່ານ Privacy Policy",
            "agreed_seller_rules": "ຂ້ອຍຮັບຮູ້ Seller Rules",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["business_registration_number"].required = False
        self.fields["verification_document"].required = False
        for agreement in ("agreed_seller_agreement", "agreed_privacy_policy", "agreed_seller_rules"):
            self.fields[agreement].required = True
