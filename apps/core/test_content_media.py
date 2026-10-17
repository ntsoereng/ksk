from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.articles.models import Article
from apps.articles.sanitizers import sanitize_rich_text
from .forms import GoogleMapsEmbedField
from .models import CaseStudy, SiteInformation


class EmbedSanitizerTests(SimpleTestCase):
    def test_images_and_captions_survive_repeated_saves(self):
        source = '<figure><img src="/media/content/photo.png" alt="The chambers" onerror="alert(1)"/><figcaption>A &amp; B</figcaption></figure>'
        cleaned = sanitize_rich_text(source)
        self.assertIn('<img src="/media/content/photo.png" alt="The chambers"', cleaned)
        self.assertIn('<figcaption>A &amp; B</figcaption>', cleaned)
        self.assertNotIn('onerror', cleaned)
        self.assertEqual(cleaned, sanitize_rich_text(cleaned))

    def test_active_image_sources_and_attributes_are_removed(self):
        for url in ['javascript:alert(1)', 'data:image/svg+xml,test', '//evil.test/a.png', '/\\evil.test/a.png', 'https://example.test/&#10;file.png']:
            self.assertNotIn('<img', sanitize_rich_text(f'<img src="{url}">'))
        self.assertNotIn('<iframe', sanitize_rich_text('<iframe src="https://evil.test"></iframe>'))

    def test_external_image_is_retained_without_styles_or_events(self):
        cleaned = sanitize_rich_text('<img src="https://example.test/photo.png" alt="A &quot;photo&quot;" style="display:none" onload="run()">')
        self.assertIn('https://example.test/photo.png', cleaned)
        self.assertIn('alt="A &quot;photo&quot;"', cleaned)
        self.assertNotIn('style=', cleaned)
        self.assertNotIn('onload=', cleaned)

    def test_map_field_accepts_iframe_or_url_and_rejects_other_hosts(self):
        field = GoogleMapsEmbedField()
        url = 'https://www.google.com/maps/embed?pb=example'
        self.assertEqual(field.clean(url), url)
        self.assertEqual(field.clean(f'<iframe src="{url}" width="600" onload="bad()"></iframe>'), url)
        self.assertEqual(field.clean(''), '')
        for value in ['https://evil.test/maps/embed', 'https://www.google.com.evil.test/maps/embed', 'http://www.google.com/maps/embed', 'https://www.google.com/search?q=test', '<iframe></iframe>']:
            with self.assertRaises(ValidationError):
                field.clean(value)


class DashboardMediaTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(email='media-editor@example.test', is_staff=True)
        self.staff.user_permissions.add(Permission.objects.get(codename='add_article'))
        self.url = reverse('core:staff_content_image_upload', args=('posts',))
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def image_file(self):
        output = BytesIO()
        Image.new('RGB', (20, 10), color='white').save(output, format='PNG')
        return SimpleUploadedFile('original.png', output.getvalue(), content_type='image/png')

    def test_upload_requires_staff_and_matching_content_permission(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.client.force_login(self.staff)
        denied = reverse('core:staff_content_image_upload', args=('case-studies',))
        self.assertEqual(self.client.post(denied, {'image': self.image_file()}).status_code, 403)

    def test_uploaded_image_can_be_saved_in_article_and_publicly_rendered(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {'image': self.image_file()})
        self.assertEqual(response.status_code, 201)
        image_url = response.json()['url']
        self.assertTrue(image_url.startswith('/media/content/posts/'))
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.get(image_url).status_code, 200)
        body = f'<figure><img src="{image_url}" alt="Office"><figcaption>Our office</figcaption></figure>'
        result = self.client.post(reverse('core:staff_content_add', args=('posts',)), {
            'title': 'Image article', 'slug': 'image-article', 'excerpt': 'Intro',
            'content': body, 'status': 'published',
        })
        self.assertEqual(result.status_code, 302)
        article = Article.objects.get(slug='image-article')
        self.assertContains(self.client.get(article.get_absolute_url()), image_url)
        editor = self.client.get(reverse('core:staff_content_add', args=('posts',)))
        self.assertContains(editor, 'data-image-insert')
        self.assertContains(editor, self.url)

    def test_invalid_and_oversized_images_are_rejected(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.url).status_code, 400)
        fake = SimpleUploadedFile('fake.png', b'<svg onload="bad()"/>', content_type='image/png')
        self.assertEqual(self.client.post(self.url, {'image': fake}).status_code, 400)
        huge = SimpleUploadedFile('huge.png', b'x' * (8 * 1024 * 1024 + 1), content_type='image/png')
        self.assertEqual(self.client.post(self.url, {'image': huge}).status_code, 400)

    def test_upload_rejects_requests_without_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertEqual(client.post(self.url, {'image': self.image_file()}).status_code, 403)

    def test_case_study_body_images_survive_save_and_render(self):
        content = '<figure><img src="/media/example.png" alt="Chart"><figcaption>Overview</figcaption></figure>'
        study = CaseStudy.objects.create(title='Example', slug='example', summary='Summary', challenge=content, approach=content, outcome=content, status='published')
        study.refresh_from_db()
        self.assertIn('<img', study.challenge)
        self.assertIn('<img', study.approach)
        self.assertIn('<img', study.outcome)
        response = self.client.get(study.get_absolute_url())
        self.assertContains(response, '<figcaption>Overview</figcaption>', count=3)

    def test_dashboard_map_setting_is_saved_and_displayed(self):
        self.client.force_login(self.staff)
        self.staff.user_permissions.add(Permission.objects.get(codename='change_siteinformation'))
        url = 'https://www.google.com/maps/embed?pb=example'
        result = self.client.post(reverse('core:staff_site_settings'), {
            'firm_name': 'Khoboko Law Chambers', 'hero_title': 'Welcome',
            'hero_cta_label': 'Contact us', 'practice_section_title': 'Services',
            'people_section_title': 'Our people', 'home_cta_title': 'Talk to us',
            'about_title': 'About us', 'people_page_title': 'Our team',
            'contact_title': 'Contact', 'google_maps_embed_url': f'<iframe src="{url}"></iframe>',
        })
        self.assertEqual(result.status_code, 302)
        self.assertEqual(SiteInformation.get_solo().google_maps_embed_url, url)
        self.assertContains(self.client.get(reverse('core:contact')), f'<iframe src="{url}"')
        SiteInformation.objects.all().delete()
        self.assertNotContains(self.client.get(reverse('core:contact')), '<iframe')

    def test_homepage_no_longer_contains_approach_or_section_numbering(self):
        response = self.client.get(reverse('core:home'))
        self.assertNotContains(response, 'The Khoboko approach')
        self.assertNotContains(response, '01 /')
        self.assertNotContains(response, '03 /')
        self.assertNotContains(response, 'service-index')
