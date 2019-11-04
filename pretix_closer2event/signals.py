from datetime import timedelta
from urllib.parse import urlparse, urlencode

from django.conf import settings
from django.contrib.staticfiles import finders
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

from pretix.base.middleware import _parse_csp, _merge_csp, _render_csp
from pretix.base.models import Order, Event
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import order_info, process_response, sass_postamble


def closer2event_params(event, ev, ev_last, order):
    p = {
        'event': event.settings.closer2event_event or 'pretix',
        'param_1': urlparse(settings.SITE_URL).hostname,
        'param_2': event.organizer.slug,
        'param_3': event.slug,
        'lang': order.locale[:2],
        # Event colors?
        # Event start date for popup?
        # Event end date for popup?
    }

    if ev.geo_lat and ev.geo_lon:
        p['center.lat'] = str(ev.geo_lat)
        p['center.lng'] = str(ev.geo_lon)
        p['markers.0.lat'] = str(ev.geo_lat)
        p['markers.0.lng'] = str(ev.geo_lon)
    else:
        pass
        # ToDo: Use a geocoding-service?

    df = ev.date_from.astimezone(event.timezone)
    p['check_in'] = (df - timedelta(days=1)).date().isoformat() if df.hour < 12 else df.date().isoformat()
    dt = max(df + timedelta(days=1), (ev_last.date_to or ev_last.date_from)).astimezone(event.timezone)
    p['check_out'] = (dt + timedelta(days=1)).date().isoformat() if dt.hour > 12 else dt.date().isoformat()

    return p


@receiver(order_info, dispatch_uid="closer2event_order_info")
def order_info(sender: Event, order: Order, **kwargs):
    subevents = {op.subevent for op in order.positions.all()}
    if sender.settings.closer2event_embedlink:
        ctx = {
            'url': sender.settings.closer2event_embedlink
        }
    else:
        ctx = {
            'url': 'https://map.closer2event.com/?{}'.format(urlencode(closer2event_params(
                sender,
                min(subevents, key=lambda s: s.date_from) if sender.has_subevents else sender,
                max(subevents, key=lambda s: s.date_to or s.date_from) if sender.has_subevents else sender,
                order
            )))
        }

    template = get_template('pretix_closer2event/order_info.html')
    return template.render(ctx)


@receiver(signal=process_response, dispatch_uid="closer2event_middleware_resp")
def signal_process_response(sender, request: HttpRequest, response: HttpResponse, **kwargs):
    if 'Content-Security-Policy' in response:
        h = _parse_csp(response['Content-Security-Policy'])
    else:
        h = {}

    _merge_csp(h, {
        'frame-src': ['https://map.closer2event.com'],
    })

    if h:
        response['Content-Security-Policy'] = _render_csp(h)
    return response


@receiver(sass_postamble, dispatch_uid="closer2event_sass_postamble")
def r_sass_postamble(sender, filename, **kwargs):
    if filename == "main.scss":
        with open(finders.find('pretix_closer2event/postamble.scss'), 'r') as fp:
            return fp.read()
    return ""


@receiver(nav_event_settings, dispatch_uid='closer2event_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(request.organizer, request.event, 'can_change_event_settings',
                                             request=request):
        return []
    return [{
        'label': _('closer2event'),
        'icon': 'house',
        'url': reverse('plugins:pretix_closer2event:settings', kwargs={
            'event': request.event.slug,
            'organizer': request.organizer.slug,
        }),
        'active': url.namespace == 'plugins:pretix_closer2event',
    }]
