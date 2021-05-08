from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User
from django import forms


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user with no usable password.
    """

    class Meta:
        model = User
        fields = ("username",)
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs['autofocus'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()
        if commit:
            user.save()
        return user
