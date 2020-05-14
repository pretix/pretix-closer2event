from datetime import timedelta
from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _  # NoQA
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.base.models import Event, Order
from pretix.base.settings import GlobalSettingsObject
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import order_info, process_response, sass_postamble


def closer2event_params(event, ev, ev_last, order):
    gs = GlobalSettingsObject()

    p = {
        'event': event.settings.closer2event_event or 'pretix',
        'param_1': urlparse(settings.SITE_URL).hostname,
        'param_2': event.organizer.slug,
        'param_3': event.slug,
        'lang': order.locale[:2],
        'header_bg': event.settings.primary_color[1:],
        'header_color': 'FFFFFF',
        'button_bg': 'FFFFFF',
        'event_inidate': event.date_from.strftime('%Y-%m-%d') or 'null',
        'event_enddate': event.date_to.strftime('%Y-%m-%d') or 'null',
    }

    if ev.geo_lat and ev.geo_lon:
        p['center.lat'] = str(ev.geo_lat)
        p['center.lng'] = str(ev.geo_lon)
        p['markers.0.lat'] = str(ev.geo_lat)
        p['markers.0.lng'] = str(ev.geo_lon)
    else:
        raise ObjectDoesNotExist('Got no lat/lng and no location and/or OpenCage API-key.')

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
        try:
            ctx = {
                'url': 'https://map.closer2event.com/?{}'.format(urlencode(closer2event_params(
                    sender,
                    min(subevents, key=lambda s: s.date_from) if sender.has_subevents and subevents else sender,
                    max(subevents, key=lambda s: s.date_to or s.date_from) if sender.has_subevents and subevents else sender,
                    order
                )))
            }
        except (IOError, ObjectDoesNotExist):
            return

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
