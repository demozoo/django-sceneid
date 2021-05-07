from django import template
from django.urls import reverse


register = template.Library()

@register.inclusion_tag('sceneid/tags/login_button_small.html', takes_context=True)
def sceneid_login_button_small(context):
    return {
        'auth_url': reverse('sceneid:auth'),
    }


@register.inclusion_tag('sceneid/tags/login_button_large.html', takes_context=True)
def sceneid_login_button_large(context):
    return {
        'auth_url': reverse('sceneid:auth'),
    }
