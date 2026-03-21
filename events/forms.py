from django import forms
from django.utils.text import slugify

from .models import Category, Event, Tag


class EventForm(forms.ModelForm):
    """Form for creating and editing events."""

    tags_input = forms.CharField(
        required=False,
        label="Tags",
        help_text="Enter comma-separated tags (e.g., ai, tech, networking)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter tags separated by commas",
        }),
    )

    class Meta:
        model = Event
        fields = (
            "title",
            "description",
            "date",
            "time",
            "location",
            "category",
            "capacity",
            "price",
            "banner",
            "is_featured",
            "latitude",
            "longitude",
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
                "placeholder": "Event location (address or venue name)",
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "Max attendees",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0.00 (free)",
            }),
            "banner": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "e.g. 12.9716 (optional)",
            }),
            "longitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "e.g. 77.5946 (optional)",
            }),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return capacity

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["tags_input"].initial = ", ".join([t.name for t in self.instance.tags.all()])

    def save(self, commit=True):
        event = super().save(commit=False)
        
        tags_str = self.cleaned_data.get("tags_input", "")
        tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
        
        if commit:
            event.save()
            tag_objs = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tag_objs.append(tag)
            event.tags.set(tag_objs)
            self.save_m2m()
        else:
            old_save_m2m = self.save_m2m
            def save_m2m():
                old_save_m2m()
                tag_objs = []
                for name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    tag_objs.append(tag)
                event.tags.set(tag_objs)
            self.save_m2m = save_m2m
            
        return event


class EventSearchForm(forms.Form):
    """Simple search/filter form for events."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Search events by title or location...",
        }),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
