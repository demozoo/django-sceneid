from urllib.parse import urlencode
from django import template
from django.urls import reverse


register = template.Library()

@register.simple_tag(takes_context=True)
def sceneid_auth_url(context, next_url=None):
    request = context.get('request')
    url = reverse('sceneid:auth')

    if next_url is None and request and request.method == 'GET':
        next_url = request.path

    if next_url:
        url += "?" + urlencode({'next': next_url})

    return url


@register.inclusion_tag('sceneid/tags/login_button_small.html', takes_context=True)
def sceneid_login_button_small(context, next_url=None):
    return {
        'auth_url': sceneid_auth_url(context, next_url),
    }


@register.inclusion_tag('sceneid/tags/login_button_large.html', takes_context=True)
def sceneid_login_button_large(context, next_url=None):
    return {
        'auth_url': sceneid_auth_url(context, next_url),
    }
