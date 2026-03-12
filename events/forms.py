from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    """Form for creating and editing events."""

    class Meta:
        model = Event
        fields = (
            "title",
            "description",
            "date",
            "time",
            "location",
            "capacity",
            "banner",
            "is_featured",
        )
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Event title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe your event...",
            }),
            "date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Event location",
            }),
            "capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "Max attendees",
            }),
            "banner": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return capacity


class EventSearchForm(forms.Form):
    """Simple search form for filtering events."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Search events by title or location...",
        }),
    )
