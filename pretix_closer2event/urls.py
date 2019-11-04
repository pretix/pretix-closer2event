from django.conf.urls import url

from .views import closer2eventSettings

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/closer2event/settings$',
        closer2eventSettings.as_view(), name='settings'),
]
