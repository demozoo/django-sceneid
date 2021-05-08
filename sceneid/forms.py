import re
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

    def __init__(self, sceneid_user_data, *args, **kwargs):
        username_field_name = self._meta.model.USERNAME_FIELD

        initial_data = kwargs.setdefault('initial', {})
        if 'display_name' in sceneid_user_data:
            clean_username = re.sub(r"[^a-z0-9A-Z]+", "", sceneid_user_data['display_name'])
            initial_data.setdefault(username_field_name, clean_username)

        initial_data.setdefault('first_name', sceneid_user_data.get('first_name'))
        initial_data.setdefault('last_name', sceneid_user_data.get('last_name'))

        super().__init__(*args, **kwargs)
        if username_field_name in self.fields:
            self.fields[username_field_name].widget.attrs['autofocus'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()
        if commit:
            user.save()
        return user
