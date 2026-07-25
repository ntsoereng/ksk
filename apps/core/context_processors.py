from .models import SiteInformation
from apps.practice_areas.models import PracticeArea


def site_information(request):
    """Make editable site information available in every template."""
    # An unsaved instance exposes model defaults so every page still has
    # complete metadata before the administrator creates the singleton record.
    information = SiteInformation.get_solo() or SiteInformation()
    canonical_url = request.build_absolute_uri(request.path)
    if information.site_url:
        canonical_url = f"{information.site_url.rstrip('/')}{request.path}"
    information.social_image_absolute_url = (
        request.build_absolute_uri(information.social_image.url)
        if information.social_image else ''
    )
    information.logo_absolute_url = (
        request.build_absolute_uri(information.logo.url)
        if information.logo else ''
    )
    return {
        'site_information': information,
        'canonical_url': canonical_url,
        'footer_practice_areas': PracticeArea.objects.filter(
            is_active=True,
        )[:5],
    }
