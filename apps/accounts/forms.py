from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


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


class SellerApplicationForm(forms.Form):
    confirm = forms.BooleanField(
        label="ຂ້ອຍຍອມຮັບວ່າຈະຂາຍສິນຄ້າຢ່າງຮັບຜິດຊອບ.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
