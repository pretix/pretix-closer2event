from django.utils.translation import gettext_lazy
from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    default = True
    name = 'pretix_closer2event'
    verbose_name = 'closer2event Hotel map'

    class PretixPluginMeta:
        name = gettext_lazy('closer2event Hotel map')
        author = 'Martin Gross'
        description = gettext_lazy('This plugin allows to integrate the closer2event hotel map into your pretix shop')
        visible = True
        category = 'INTEGRATION'
        version = __version__
        compatibility = "pretix>=3.2.999"

    def ready(self):
        from . import signals  # NOQA

