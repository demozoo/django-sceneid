django-sceneid
==============

[SceneID](https://id.scene.org/) authentication for Django

Installation
------------

To install:

```shell
pip install django-sceneid
```

Add `'sceneid'` to your project's `INSTALLED_APPS`, then run `./manage.py migrate`.

In your project's top-level URL config, include the URLconf `sceneid.urls`:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path('account/sceneid/', include('sceneid.urls')),
    # ...
]
```

At this point you'll need to [obtain an API key from scene.org](https://id.scene.org/docs/#api-keys). They'll want to know your redirect URI, which is the path you used above with `login/` appended; for example `https://demosite.example.com/account/sceneid/login/`. Once you have this, add the following settings to your project's settings file:

```python
# The client ID you received from scene.org
SCENEID_CLIENT_ID = 'demosite'
# The client secret you received from scene.org
SCENEID_CLIENT_SECRET = 'supersecretclientsecret'
# The root URL of your website, without a trailing slash
BASE_URL = 'https://demosite.example.com'
# Where to redirect to after login (defaults to /accounts/profile/)
LOGIN_REDIRECT_URL = '/'
```

Integrating into your site
--------------------------

The simplest way to add a 'sign in with SceneID' button to your site is to add the `sceneid_login_button_small` or `sceneid_login_button_large` template tag in a suitable place on your template:

```html+django
{% load sceneid_tags %}  {# must be at the top of your template #}

{% if not request.user.is_authenticated %}
    {% sceneid_login_button_large %}
{% endif %}
```

This will output a button linking to the login view, with a 'next' parameter that will redirect back to the current page after login (unless the current page is a POST request, in which case this will be omitted). To override this, pass a `next_url` parameter to the tag - this can be the desired redirect URL, or False to disable it entirely.

```html+django
{% sceneid_login_button_large next_url='/some/other/path/' %}

{% sceneid_login_button_large next_url=False %}
```
