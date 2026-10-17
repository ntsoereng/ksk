from datetime import datetime, timezone as datetime_timezone
from ipaddress import ip_address, ip_network
import math
import time

from django.conf import settings
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import FormRateLimit


def client_address(request):
    """Trust forwarded addresses only when the immediate peer is configured."""
    try:
        peer = ip_address(request.META.get('REMOTE_ADDR', ''))
    except ValueError:
        return 'unknown'
    networks = [ip_network(value) for value in settings.FORM_TRUSTED_PROXIES]

    def trusted(address):
        return any(address in network for network in networks)

    if not trusted(peer):
        return str(peer)
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        chain = [ip_address(value.strip()) for value in forwarded.split(',')]
    except ValueError:
        return str(peer)
    for address in reversed(chain):
        if not trusted(address):
            return str(address)
    return str(peer)


def consume_limit(scope, identity):
    """Atomically consume one request; return seconds to wait, or zero."""
    limit, seconds = settings.FORM_RATE_LIMITS[scope]
    now = time.time()
    window = int(now // seconds)
    reset = (window + 1) * seconds
    key = salted_hmac('form-rate-limit', f'{scope}:{identity}:{window}', algorithm='sha256').hexdigest()
    counter, created = FormRateLimit.objects.get_or_create(
        key=key,
        defaults={'expires_at': datetime.fromtimestamp(reset, tz=datetime_timezone.utc)},
    )
    if created:
        # Bound cleanup work on new counters; no scheduled job is required.
        expired = list(FormRateLimit.objects.filter(expires_at__lte=timezone.now()).exclude(pk=counter.pk).values_list('pk', flat=True)[:100])
        if expired:
            FormRateLimit.objects.filter(pk__in=expired).delete()
    admitted = FormRateLimit.objects.filter(pk=counter.pk, count__lt=limit).update(count=F('count') + 1)
    return 0 if admitted else max(1, math.ceil(reset - now))
