from .models import SiteInformation
from apps.practice_areas.models import PracticeArea
from .seo import absolute_url, public_origin


def site_information(request):
    """Make editable site information available in every template."""
    # An unsaved instance exposes model defaults so every page still has
    # complete metadata before the administrator creates the singleton record.
    information = SiteInformation.get_solo() or SiteInformation()
    origin = public_origin(request, information)
    canonical_url = absolute_url(origin, request.path)
    information.social_image_absolute_url = (
        absolute_url(origin, information.social_image.url)
        if information.social_image else ''
    )
    information.logo_absolute_url = (
        absolute_url(origin, information.logo.url)
        if information.logo else ''
    )
    return {
        'site_information': information,
        'canonical_url': canonical_url,
        'footer_practice_areas': PracticeArea.objects.filter(
            is_active=True,
        )[:5],
    }
