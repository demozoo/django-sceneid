django-sceneid
==============

[SceneID](https://id.scene.org/) authentication for Django

Installation
------------

To install:

```shell
pip install django-sceneid
```

Add `'sceneid'` to your project's `INSTALLED_APPS`.

In your project's top-level URL config, include the URLconf `sceneid.urls`:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path('account/sceneid/', include('sceneid.urls')),
    # ...
]
```
