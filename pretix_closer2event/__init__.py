from django.utils.translation import ugettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    name = 'pretix_closer2event'
    verbose_name = 'closer2event Hotel map'

    class PretixPluginMeta:
        name = ugettext_lazy('closer2event Hotel map')
        author = 'Martin Gross'
        description = ugettext_lazy('This plugin allows to integrate the closer2event hotel map into your pretix shop')
        visible = True
        category = 'INTEGRATION'
        version = '1.0.1'
        compatibility = "pretix>=3.2.999"

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_closer2event.PluginApp'
