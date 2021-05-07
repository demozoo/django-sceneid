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
```
