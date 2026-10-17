"""Shared public URL handling for metadata and crawler endpoints."""
from urllib.parse import urljoin, urlsplit

from django.conf import settings


def public_origin(request=None, information=None):
    configured = settings.SITE_URL or getattr(information, 'site_url', '')
    if configured:
        parts = urlsplit(configured)
        return f'{parts.scheme}://{parts.netloc}'
    return request.build_absolute_uri('/').rstrip('/') if request else ''


def absolute_url(origin, path):
    return urljoin(f'{origin}/', path)
