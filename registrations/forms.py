from django import forms


class RegistrationForm(forms.Form):
    """
    Minimal confirmation form for event registration.
    """

    confirm = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.HiddenInput(),
    )


class CustomRegistrationForm(forms.Form):
    """
    Dynamic form that generates fields based on an event's CustomField records.
    """

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        super().__init__(*args, **kwargs)

        # Build dynamic fields from the event's custom fields
        for field in self.event.custom_fields.all():
            field_name = f"custom_{field.id}"
            if field.field_type == "text":
                self.fields[field_name] = forms.CharField(
                    label=field.label,
                    required=field.required,
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": field.placeholder or "",
                        }
                    ),
                )
            elif field.field_type == "textarea":
                self.fields[field_name] = forms.CharField(
                    label=field.label,
                    required=field.required,
                    widget=forms.Textarea(
                        attrs={
                            "class": "form-control",
                            "rows": 3,
                            "placeholder": field.placeholder or "",
                        }
                    ),
                )
            elif field.field_type == "select":
                self.fields[field_name] = forms.ChoiceField(
                    label=field.label,
                    required=field.required,
                    choices=[("", "--- Select Option ---")] + field.get_choices(),
                    widget=forms.Select(attrs={"class": "form-select"}),
                )
            elif field.field_type == "checkbox":
                self.fields[field_name] = forms.BooleanField(
                    label=field.label,
                    required=field.required,
                    widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                )
