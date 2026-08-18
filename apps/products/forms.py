from django import forms

from .models import Product, Review, SubCategory


class ProductForm(forms.ModelForm):
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(),
        required=False,
        empty_label="ເລືອກໝວດຍ່ອຍ",
    )

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "subcategory",
            "description",
            "price",
            "stock",
            "image",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ຊື່ສິນຄ້າ"}
            ),
            "category": forms.Select(
                attrs={"class": "form-select"}
            ),
            "subcategory": forms.Select(
                attrs={"class": "form-select"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "ລາຍລະອຽດສິນຄ້າ",
                }
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "stock": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "image": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }
        labels = {
            "name": "ຊື່ສິນຄ້າ",
            "category": "ໝວດໝູ່",
            "subcategory": "ໝວດຍ່ອຍ",
            "description": "ລາຍລະອຽດ",
            "price": "ລາຄາ",
            "stock": "ຈຳນວນໃນສາງ",
            "image": "ຮູບຫຼັກ",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category = self.instance.category if self.instance and self.instance.pk else None

        if category is not None:
            self.fields["subcategory"].queryset = SubCategory.objects.filter(category=category)
        elif self.data.get("category"):
            try:
                category_id = int(self.data.get("category"))
            except (TypeError, ValueError):
                category_id = None
            if category_id:
                self.fields["subcategory"].queryset = SubCategory.objects.filter(category_id=category_id)

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        subcategory = cleaned_data.get("subcategory")

        if subcategory and category and subcategory.category_id != category.pk:
            raise forms.ValidationError("ໝວດຍ່ອຍທີ່ເລືອກຕ້ອງຢູ່ໃນໝວດໝູ່ທີ່ເລືອກ.")

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} ດາວ") for i in range(1, 6)], attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {"rating": "ຄະແນນ", "comment": "ຄຳເຫັນ"}
