from django import forms


class RegistrationForm(forms.Form):
    """
    Minimal confirmation form for event registration.
    The actual validation lives in the view — this form exists
    for CSRF protection and as a hook for future fields.
    """

    confirm = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.HiddenInput(),
    )
