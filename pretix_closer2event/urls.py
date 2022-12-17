from django.urls import path

from .views import Closer2eventSettings

urlpatterns = [
    path('control/event/<str:organizer>/<str:event>/closer2event/settings',
         Closer2eventSettings.as_view(), name='settings'),
]
