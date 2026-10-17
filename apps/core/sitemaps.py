from django.urls import reverse
from django.utils import timezone
from django.contrib.sitemaps import Sitemap
from types import SimpleNamespace
from urllib.parse import urlsplit

from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea
from .models import CaseStudy, SiteInformation
from .seo import public_origin


class PublicSitemap(Sitemap):
    def get_urls(self, page=1, site=None, protocol=None):
        origin = public_origin(information=SiteInformation.get_solo())
        if origin:
            parts = urlsplit(origin)
            site = SimpleNamespace(domain=parts.netloc)
            protocol = parts.scheme
        return super().get_urls(page=page, site=site, protocol=protocol)


class StaticViewSitemap(PublicSitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return ('core:home', 'core:about', 'core:contact', 'practice_areas:list',
                'core:case_study_list', 'attorneys:list', 'articles:list',
                'core:privacy', 'core:terms')

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'core:home' else 0.7


class PracticeAreaSitemap(PublicSitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return PracticeArea.objects.filter(is_active=True)


class AttorneySitemap(PublicSitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return Attorney.objects.filter(is_active=True).select_related('user')


class ArticleSitemap(PublicSitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )

    def lastmod(self, obj):
        return obj.updated_at


class CaseStudySitemap(PublicSitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return CaseStudy.objects.filter(
            status=CaseStudy.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    'static': StaticViewSitemap,
    'practice-areas': PracticeAreaSitemap,
    'people': AttorneySitemap,
    'articles': ArticleSitemap,
    'case-studies': CaseStudySitemap,
}
