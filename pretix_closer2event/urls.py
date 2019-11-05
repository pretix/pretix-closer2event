from django.conf.urls import url

from .views import Closer2eventSettings

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/closer2event/settings$',
        Closer2eventSettings.as_view(), name='settings'),
]
