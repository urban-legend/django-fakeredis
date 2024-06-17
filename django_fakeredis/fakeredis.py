import os
import fakeredis
import pkgutil
from unittest.mock import patch, _get_target

from django.test import override_settings

server = fakeredis.FakeServer()


def get_fake_redis():
    """ mock the same redis connection """
    return fakeredis.FakeStrictRedis(server=server)


class FakeRedis:
    """
    Combine override settings:  CACHE and  fakeredis
    To disable the fake action with passing env: "NOFAKE_REDIS=1"
    """

    NOFAKE_REDIS = True if "NOFAKE_REDIS" in os.environ else False

    def __init__(self, path):
        self.path = path
        self.override_settings = None
        self.patch = None

        if not self.NOFAKE_REDIS:
            # We have to override CACHE settings for django_redis too
            self.override_settings = override_settings(
                CACHES={
                    "default": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache"
                    }
                }
            )
            # Recheck path in mock lib
            _get_target(path)
            target = pkgutil.resolve_name(path)
            if callable(target):
                self.patch = patch(self.path, get_fake_redis)
            else:
                # Here the mock target is django.cache
                pass

    def __call__(self, fn):
        if not self.NOFAKE_REDIS:
            fn = self.override_settings(fn)
            if self.patch:
                fn = self.patch(fn)

        return fn

    def __enter__(self):
        if not self.NOFAKE_REDIS:
            if self.override_settings and self.patch:
                return self.override_settings.__enter__(), self.patch.__enter__()
            elif self.override_settings:
                return self.override_settings.__enter__()
            elif self.patch:
                return self.patch.__enter__()

        return None

    def __exit__(self, *args, **kw):
        if not self.NOFAKE_REDIS:
            if self.override_settings:
                self.override_settings.__exit__(*args, **kw)
            if self.patch:
                self.patch.__exit__(*args, **kw)
