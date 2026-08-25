"""Small presentation helpers for the Lao Django administration interface."""


def apply_lao_labels(fields, labels, choice_labels=None):
    """Apply display labels to a dictionary of Django form fields."""
    for field_name, label in labels.items():
        field = fields.get(field_name)
        if field is None:
            continue
        field.label = label
        if choice_labels and field_name in choice_labels:
            translated_choices = choice_labels[field_name]
            field.choices = [
                (value, translated_choices.get(value, display))
                for value, display in field.choices
            ]


class LaoAdminMixin:
    """Add Lao labels to a ModelAdmin form without changing database schema."""

    field_labels = {}
    choice_labels = {}

    def get_form(self, request, obj=None, change=False, **kwargs):
        # Passed as a keyword, not positionally: some ModelAdmin subclasses
        # (e.g. django.contrib.auth.admin.UserAdmin) override get_form with a
        # narrower signature that has no positional slot for `change`.
        form = super().get_form(request, obj, change=change, **kwargs)
        apply_lao_labels(form.base_fields, self.field_labels, self.choice_labels)
        return form


class LaoInlineMixin:
    """Add Lao labels to fields displayed in an inline ModelAdmin formset."""

    field_labels = {}
    choice_labels = {}

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        apply_lao_labels(formset.form.base_fields, self.field_labels, self.choice_labels)
        return formset
