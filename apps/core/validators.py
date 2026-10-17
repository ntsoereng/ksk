from urllib.parse import urlsplit

from django.core.exceptions import ValidationError


def validate_google_maps_embed_url(value):
    if not value:
        return
    try:
        url = urlsplit(value)
        valid = (
            url.scheme == 'https'
            and url.netloc in {'www.google.com', 'google.com', 'maps.google.com'}
            and (url.path == '/maps/embed' or url.path.startswith('/maps/embed/'))
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValidationError('Use the Google Maps “Share → Embed a map” URL or iframe code.')
