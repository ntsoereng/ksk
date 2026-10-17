import json
from datetime import timedelta
from html.parser import HTMLParser
from xml.etree import ElementTree

from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from PIL import Image

from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea
from .models import CaseStudy, SiteInformation


class HeadParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.links = {}
        self.title = ''
        self.structured = ''
        self.capture = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name') or attrs.get('property')] = attrs.get('content')
        if tag == 'link':
            self.links[attrs.get('rel')] = attrs.get('href')
        if tag == 'title':
            self.capture = 'title'
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.capture = 'structured'

    def handle_data(self, data):
        if self.capture:
            setattr(self, self.capture, getattr(self, self.capture) + data)

    def handle_endtag(self, tag):
        if tag in {'title', 'script'}:
            self.capture = None


@override_settings(SITE_URL='', SECURE_SSL_REDIRECT=False)
class PublicSeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.info = SiteInformation.objects.create(
            firm_name="Khoboko's Chambers & Partners",
            site_url='https://law.example', primary_email='reports@law.example',
        )
        cls.area = PracticeArea.objects.create(
            name='Property law', slug='property-law',
            short_description='Practical property advice.', description='<p>Legal services.</p>',
        )
        user = get_user_model().objects.create_user(
            email='private@law.example', first_name='Mpho', last_name='Khoboko',
        )
        cls.person = Attorney.objects.create(
            user=user, title='Partner', slug='mpho-khoboko', biography='<p>Trusted advice &amp; careful preparation.</p>',
        )
        cls.article = Article.objects.create(
            title='Property & business updates', slug='property-update', excerpt='A useful legal update.',
            content='<p>Update.</p>', author=user, status=Article.Status.PUBLISHED,
        )
        cls.study = CaseStudy.objects.create(
            title='A property matter', slug='property-matter', summary='A practical approach.',
            status=CaseStudy.Status.PUBLISHED,
        )

    def head(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return HeadParser(response.content.decode())

    def test_all_public_pages_have_consistent_unique_metadata(self):
        routes = ['core:home', 'core:about', 'core:contact', 'core:privacy', 'core:terms',
                  'core:case_study_list', 'practice_areas:list', 'attorneys:list', 'articles:list']
        paths = [reverse(route) for route in routes] + [
            obj.get_absolute_url() for obj in [self.area, self.person, self.article, self.study]
        ]
        titles = set()
        descriptions = set()
        for path in paths:
            with self.subTest(path=path):
                head = self.head(path + '?utm_source=campaign')
                self.assertEqual(head.links['canonical'], 'https://law.example' + path)
                self.assertEqual(head.meta['og:url'], head.links['canonical'])
                self.assertEqual(head.meta['og:title'], head.title)
                self.assertEqual(head.meta['twitter:title'], head.title)
                self.assertEqual(head.meta['og:description'], head.meta['description'])
                self.assertEqual(head.meta['twitter:description'], head.meta['description'])
                self.assertTrue(head.meta['og:image'].startswith('https://law.example/'))
                self.assertEqual(head.meta['twitter:image'], head.meta['og:image'])
                self.assertTrue(head.meta['og:image:alt'])
                self.assertNotIn('<p>', head.meta['description'])
                self.assertLessEqual(len(head.meta['description']), 170)
                graph = json.loads(head.structured)['@graph']
                self.assertIn('LegalService', [item['@type'] for item in graph])
                self.assertIn('index, follow', head.meta['robots'])
                titles.add(head.title)
                descriptions.add(head.meta['description'])
        self.assertEqual(len(titles), len(paths))
        self.assertEqual(len(descriptions), len(paths))

    def test_article_schema_dates_author_and_breadcrumbs(self):
        head = self.head(self.article.get_absolute_url())
        graph = json.loads(head.structured)['@graph']
        article = next(item for item in graph if item['@type'] == 'BlogPosting')
        self.assertEqual(article['author']['name'], 'Mpho Khoboko')
        self.assertNotIn('private@law.example', head.structured)
        self.assertEqual(article['datePublished'], self.article.published_at.isoformat())
        self.assertEqual(head.meta['og:type'], 'article')
        self.assertTrue(head.meta['article:published_time'])
        crumbs = next(item for item in graph if item['@type'] == 'BreadcrumbList')
        self.assertEqual([item['position'] for item in crumbs['itemListElement']], [1, 2, 3])

    def test_content_images_override_default_and_preserve_cdn_urls(self):
        self.info.social_image = 'site/social/default.png'
        self.info.save()
        head = self.head(self.article.get_absolute_url())
        self.assertEqual(head.meta['og:image'], 'https://law.example/media/site/social/default.png')
        self.article.featured_image = 'articles/cover.png'
        self.article.save()
        head = self.head(self.article.get_absolute_url())
        self.assertEqual(head.meta['og:image'], 'https://law.example/media/articles/cover.png')
        # Recreate the configured storage: SafeMediaStorage captures its base
        # URL when instantiated, as it does at process startup in production.
        storages = {**settings.STORAGES, 'default': {
            'BACKEND': 'apps.core.storage.SafeMediaStorage',
            'OPTIONS': {'base_url': 'https://cdn.example/media/'},
        }}
        with override_settings(STORAGES=storages):
            head = self.head(self.article.get_absolute_url())
            self.assertEqual(head.meta['og:image'], 'https://cdn.example/media/articles/cover.png')

    def test_bundled_fallback_card_is_available_without_site_settings(self):
        self.info.delete()
        head = self.head('/')
        self.assertIn('/static/images/branding/social-preview', head.meta['og:image'])
        with Image.open(finders.find('images/branding/social-preview.png')) as image:
            self.assertEqual(image.size, (1200, 630))

    def test_structured_data_is_valid_json_and_cannot_close_script(self):
        self.info.firm_name = "Counsel's </script><script>alert(1)</script> & Partners"
        self.info.save()
        head = self.head(reverse('core:home'))
        self.assertNotIn('</script>', head.structured)
        self.assertEqual(json.loads(head.structured)['@graph'][0]['name'], self.info.firm_name)

    def test_sitemap_and_robots_use_canonical_origin_and_public_content_only(self):
        hidden = PracticeArea.objects.create(
            name='Hidden service', slug='hidden-service', is_active=False,
        )
        draft = Article.objects.create(title='Draft', slug='draft', excerpt='Draft')
        future = CaseStudy.objects.create(
            title='Future', slug='future', status=CaseStudy.Status.PUBLISHED,
            published_at=timezone.now() + timedelta(days=2),
        )
        response = self.client.get(reverse('sitemap'))
        root = ElementTree.fromstring(response.content)
        urls = [node.text for node in root.findall('{*}url/{*}loc')]
        for obj in [self.area, self.person, self.article, self.study]:
            self.assertIn('https://law.example' + obj.get_absolute_url(), urls)
        for obj in [hidden, draft, future]:
            self.assertNotIn('https://law.example' + obj.get_absolute_url(), urls)
            self.assertEqual(self.client.get(obj.get_absolute_url()).status_code, 404)
        self.assertIn('https://law.example/privacy/', urls)
        self.assertIn('https://law.example/terms/', urls)
        self.assertFalse(any('/staff/' in url or '/admin/' in url for url in urls))
        robots = self.client.get(reverse('robots'))
        self.assertContains(robots, 'Disallow: /staff/')
        self.assertContains(robots, 'Disallow: /admin/')
        self.assertContains(robots, 'Sitemap: https://law.example/sitemap.xml')

    @override_settings(SITE_URL='https://production.example/')
    def test_deployment_origin_overrides_editable_url_everywhere(self):
        head = self.head(reverse('core:about'))
        self.assertEqual(head.links['canonical'], 'https://production.example/about/')
        for route in ['sitemap', 'robots', 'security']:
            response = self.client.get(reverse(route))
            self.assertContains(response, 'https://production.example/')
            self.assertNotContains(response, 'https://law.example/')

    def test_security_contact_fallback_expiry_and_legacy_redirect(self):
        response = self.client.get(reverse('security'))
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertContains(response, 'Contact: mailto:reports@law.example\n')
        self.assertContains(response, 'Canonical: https://law.example/.well-known/security.txt\n')
        lines = dict(line.split(': ', 1) for line in response.content.decode().splitlines())
        self.assertIsNotNone(parse_datetime(lines['Expires']).tzinfo)
        self.assertRedirects(self.client.get('/security.txt'), reverse('security'), status_code=301)
        with override_settings(SECURITY_CONTACT='https://security.example/report'):
            self.assertContains(self.client.get(reverse('security')), 'Contact: https://security.example/report\n')
        self.info.primary_email = ''
        self.info.save()
        self.assertContains(self.client.get(reverse('security')), 'Contact: https://law.example/contact/\n')

    def test_private_routes_and_errors_are_noindex(self):
        for path in ['/staff/', '/staff/login/', '/admin/', '/admin/login/', '/missing-page/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        self.assertNotIn('X-Robots-Tag', self.client.get('/'))
