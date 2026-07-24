from django.urls import reverse
from django.utils import timezone
from django.contrib.sitemaps import Sitemap

from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea


class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return ('core:home', 'core:about', 'core:contact', 'practice_areas:list',
                'attorneys:list', 'articles:list')

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'core:home' else 0.7


class PracticeAreaSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return PracticeArea.objects.filter(is_active=True)


class AttorneySitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return Attorney.objects.filter(is_active=True).select_related('user')


class ArticleSitemap(Sitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    'static': StaticViewSitemap,
    'practice-areas': PracticeAreaSitemap,
    'people': AttorneySitemap,
    'articles': ArticleSitemap,
}
