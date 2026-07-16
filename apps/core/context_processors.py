from .models import SiteInformation


def site_information(request):
    """Make editable site information available in every template."""
    return {'site_information': SiteInformation.get_solo()}
