from pelican.settings import DEFAULT_CONFIG, configure_settings
import pelican
import copy
import six


def combine(d1, d2):
    d3 = copy.deepcopy(d1)
    d3.update(d2)
    return d3


def initialize_settings(settings):
    return configure_settings(combine(DEFAULT_CONFIG, settings))


def patch_pelican_settings(settings_without_default):
    settings = initialize_settings(settings_without_default)

    def get_instance(_):
        cls = settings['PELICAN_CLASS']
        if isinstance(cls, six.string_types):
            module, cls_name = cls.rsplit('.', 1)
            module = __import__(module)
            cls = getattr(module, cls_name)

        return cls(settings), settings

    pelican.get_instance = get_instance
    return settings
