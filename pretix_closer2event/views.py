from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _  # NoQA
from pretix.base.forms import SettingsForm
from pretix.base.models import Event
from pretix.control.views.event import (
    EventSettingsFormView, EventSettingsViewMixin,
)


class Closer2eventSettingsForm(SettingsForm):
    closer2event_event = forms.CharField(
        label=_("closer2event event ID"),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'pretix'})
    )
    closer2event_embedlink = forms.CharField(
        label=_("closer2event Embed Link"),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'https://map.closer2event.com/?event=pretix'})
    )


class Closer2eventSettings(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = Closer2eventSettingsForm
    template_name = 'pretix_closer2event/settings.html'
    permission = 'can_change_settings'

    def get_success_url(self) -> str:
        return reverse('plugins:pretix_closer2event:settings', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug
        })
