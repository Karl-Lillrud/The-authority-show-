from .exceptions import ConfigurationError
from .env import DJANGO_CONFIGURED, DJANGO_SETTINGS


class Conf(object):
    _namespace = None
    _settings = None
    _has_been_configured = False
    _configured_from_env = False

    def __init__(self, namespace, settings):
        self._namespace = namespace
        self._settings = settings
        if DJANGO_CONFIGURED:
            overrides = getattr(DJANGO_SETTINGS, self._namespace, None)
            if overrides:
                self.configure(overrides)
                self._configured_from_env = True

    def configure(self, overrides):
        if self._has_been_configured:
            raise ConfigurationError('{namespace} already configured'.format(namespace=self._namespace))
        self._has_been_configured = True
        self._settings.update(overrides)

    def get(self, name, default=None):
        if name in self._settings:
            return getattr(self, name)
        return default

    def keys(self):
        return self._settings.keys()

    def __getattr__(self, name):
        if name in self._settings:
            return self._settings[name]
        raise ConfigurationError('setting "{name}" has not been defined'.format(name=name))
