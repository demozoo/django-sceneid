django-sceneid
==============

[SceneID](https://id.scene.org/) authentication for Django

How it works
------------

It's assumed that your website has an existing login system, based on [Django's authentication framework](https://docs.djangoproject.com/en/stable/topics/auth/). SceneID does not replace it - the ability to log in via SceneID will be offered as an alternative alongside the standard login form. The existing User model will continue to be used, regardless of whether a user logs in through SceneID or a regular username / password.

The 'Sign in with SceneID' link will authenticate the user against SceneID. If the SceneID account is already associated with a user account on the website (as stored in the database under the sceneid.SceneID model), that user is immediately logged in and your website can refer to `request.user` as normal. Otherwise, the user is redirected to a 'connect' view, prompting them to either log in with an existing username / password, or register a new account (in which case they'll be prompted for a username and other required fields, but not password). In both cases, the resulting user account will be linked to the SceneID account so that they can log in immediately next time.

Demo site (including much of the configuration and customisation described below) - https://github.com/demozoo/django-sceneid-demosite

Installation
------------

django-sceneid is compatible with Django 3.x and 4.x. To install:

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

If you don't want to use the button images, the `sceneid_auth_url` tag outputs just the URL, to be inserted into a link of your choice. This tag also accepts a `next_url` parameter, as well as supporting the `as var` syntax to write the result to a variable:

```html+django
{% sceneid_auth_url next_url='/some/other/path/' as auth_url %}
<a href="{{ auth_url }}">Sign in with SceneID</a>
```

Customisation
-------------

At minimum, you'll probably want to customise the template for the 'connect' view to match your site styling. The quick-and-dirty way to do this is to create a template with the path `sceneid/connect.html` within one of your apps, and ensuring that template takes precedence over the default one by placing that app's entry above `'sceneid'`in `INSTALLED_APPS`. This template receives the following context variables:

* `user_data` - the dictionary of user data [returned from SceneID](https://id.scene.org/docs/#cmd-me), consisting of `id`, `first_name`, `last_name` and `display_name`
* `login_form` - a [Django form object](https://docs.djangoproject.com/en/stable/topics/forms/#the-template) for the login form, to be POSTed to `{% url 'sceneid:connect_old' %}`
* `register_form` - a [Django form object](https://docs.djangoproject.com/en/stable/topics/forms/#the-template) for the registration form, to be POSTed to `{% url 'sceneid:connect_new' %}`

For more control over customisations, you can [override the AppConfig](https://docs.djangoproject.com/en/stable/ref/applications/#for-application-users) for the `sceneid` app. Within your project-level configuration folder (i.e. the one containing the `settings` and `urls` submodules), add the following to `apps.py`:

```python
from sceneid.apps import SceneIDConfig

class DemositeSceneIDConfig(SceneIDConfig):
    connect_template_name = 'accounts/connect.html'
```

Then replace the `'sceneid'` entry in `INSTALLED_APPS` with the dotted path to the AppConfig class:

```python
INSTALLED_APPS = [
    # ...
    'demosite.apps.DemositeSceneIDConfig',
    # ...
]
```

The template path specified in `connect_template_name` will then be used for the 'connect' view.

Custom forms
------------

The form classes used for the login and registration forms are also configurable from the AppConfig class:

* `connect_login_form_class` (default: `'django.contrib.auth.forms.AuthenticationForm'`)
* `connect_register_form_class` (default: `'sceneid.forms.UserCreationForm'`)

In particular, the provided `UserCreationForm` can be subclassed to add extra fields to the data collected on account creation. For example, to include fields for first name and last name (which will then populate the corresponding fields on the standard Django user model):

```python
# accounts/forms.py
from sceneid.forms import UserCreationForm as BaseUserCreationForm

class SceneIDUserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name')
```

```python
# demosite/apps.py
from sceneid.apps import SceneIDConfig

class DemositeSceneIDConfig(SceneIDConfig):
    connect_template_name = 'accounts/connect.html'
    connect_register_form_class = 'accounts.forms.SceneIDUserCreationForm'
```

The base `UserCreationForm` class recognises the field names `first_name` and `last_name` where present and pre-populates these from the SceneID data, in addition to pre-populating the `username` field with a cleaned version of the SceneID display name.

Using django-sceneid with [a custom User model](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model) is currently untested. The base `UserCreationForm` assumes the presence of a `'username'` field and will need to be customised accordingly if this is not the case (e.g. if your site uses email as a user's identifier instead), but all other functionality (including the login form) should work unchanged.
