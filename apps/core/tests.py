from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import BytesIO
from unittest.mock import patch

from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea

from .models import Inquiry, SiteInformation


class SeoTests(TestCase):
    def test_pages_have_canonical_metadata_and_fallback_favicon(self):
        response = self.client.get(reverse('core:home'))

        self.assertContains(response, '<link rel="canonical"', html=False)
        self.assertContains(response, '/favicon.ico')
        self.assertContains(response, 'application/ld+json')

    def test_editable_seo_metadata_is_rendered(self):
        SiteInformation.objects.create(
            firm_name='Example Law',
            site_url='https://example.test',
            seo_title='Example Legal Counsel',
            seo_description='A carefully written search description.',
        )

        response = self.client.get(reverse('core:home'))

        self.assertContains(response, '<title>Example Legal Counsel</title>', html=False)
        self.assertContains(response, 'A carefully written search description.')
        self.assertContains(response, 'https://example.test/')

    def test_robots_references_sitemap(self):
        response = self.client.get(reverse('robots'))

        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, '/sitemap.xml')

    def test_sitemap_is_available(self):
        response = self.client.get(reverse('sitemap'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertContains(response, '<loc>http://testserver/</loc>')

    def test_root_favicon_url_streams_fallback_asset(self):
        response = self.client.get(reverse('favicon'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'<svg'))
        self.assertEqual(
            response['Cache-Control'],
            'public, max-age=3600, must-revalidate',
        )

    def test_media_url_is_routed_when_django_serves_uploads(self):
        match = resolve('/media/attorneys/example.png')

        self.assertEqual(match.url_name, 'media')
        self.assertEqual(match.kwargs['path'], 'attorneys/example.png')

    @patch('apps.core.views.default_storage')
    def test_media_fallback_streams_from_configured_storage(self, storage):
        storage.exists.return_value = True
        storage.open.return_value = BytesIO(b'example-image-bytes')

        response = self.client.get('/media/attorneys/example.png')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(
            b''.join(response.streaming_content),
            b'example-image-bytes',
        )
        storage.open.assert_called_once_with('attorneys/example.png', 'rb')


class StaffDashboardTests(TestCase):
    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse('core:staff_dashboard'))

        self.assertRedirects(
            response,
            f"{reverse('core:staff_login')}?next={reverse('core:staff_dashboard')}",
        )

    def test_staff_can_review_dashboard_totals(self):
        staff = get_user_model().objects.create_superuser(
            email='staff@example.com',
            password='safe-test-password',
            first_name='Mpho',
        )
        Inquiry.objects.create(
            name='Client',
            email='client@example.com',
            subject='Property matter',
            message='Please contact me.',
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('core:staff_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, Mpho')
        self.assertContains(response, 'Property matter')
        self.assertContains(response, 'Unread messages')

    def test_non_staff_account_cannot_sign_into_portal(self):
        get_user_model().objects.create_user(
            email='visitor@example.com',
            password='safe-test-password',
        )

        response = self.client.post(reverse('core:staff_login'), {
            'username': 'visitor@example.com',
            'password': 'safe-test-password',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'authorised staff only')

    def test_staff_can_create_and_safely_format_post_on_front_end(self):
        staff = get_user_model().objects.create_superuser(
            email='editor@example.com',
            password='safe-test-password',
        )
        self.client.force_login(staff)

        editor = self.client.get(
            reverse('core:staff_content_add', args=('posts',)),
        )
        self.assertContains(editor, 'rich-text-editor')

        response = self.client.post(
            reverse('core:staff_content_add', args=('posts',)),
            {
                'title': 'A useful legal update',
                'slug': 'useful-legal-update',
                'excerpt': 'A short summary of this update.',
                'content': '<h2>Update</h2><script>alert(1)</script><p>Safe text.</p>',
                'status': Article.Status.DRAFT,
                'published_at': '',
            },
        )

        self.assertRedirects(
            response,
            reverse('core:staff_content_list', args=('posts',)),
        )
        article = Article.objects.get(slug='useful-legal-update')
        self.assertEqual(article.author, staff)
        self.assertIn('<h2>Update</h2>', article.content)
        self.assertNotIn('<script>', article.content)

    def test_staff_can_manage_message_status_on_front_end(self):
        staff = get_user_model().objects.create_superuser(
            email='messages@example.com',
            password='safe-test-password',
        )
        inquiry = Inquiry.objects.create(
            name='Sender',
            email='sender@example.com',
            subject='Advice',
            message='Please contact me.',
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse('core:staff_message_detail', args=(inquiry.pk,)),
        )

        self.assertRedirects(
            response,
            reverse('core:staff_message_detail', args=(inquiry.pk,)),
        )
        inquiry.refresh_from_db()
        self.assertTrue(inquiry.is_read)

    def test_staff_creates_person_without_selecting_internal_user(self):
        staff = get_user_model().objects.create_superuser(
            email='people-editor@example.com',
            password='safe-test-password',
        )
        self.client.force_login(staff)

        editor = self.client.get(
            reverse('core:staff_content_add', args=('people',)),
        )
        self.assertNotContains(editor, 'name="user"')
        self.assertContains(editor, 'name="first_name"')
        self.assertContains(editor, 'name="person_email"')

        response = self.client.post(
            reverse('core:staff_content_add', args=('people',)),
            {
                'first_name': 'Lerato',
                'last_name': 'Mokoena',
                'person_email': 'lerato@example.com',
                'title': 'Associate',
                'member_type': Attorney.MemberType.LAWYER,
                'slug': 'lerato-mokoena',
                'biography': '<p>Legal professional biography.</p>',
                'display_order': 1,
                'is_active': 'on',
            },
        )

        self.assertRedirects(
            response,
            reverse('core:staff_content_list', args=('people',)),
        )
        profile = Attorney.objects.select_related('user').get(
            slug='lerato-mokoena',
        )
        self.assertEqual(profile.user.first_name, 'Lerato')
        self.assertEqual(profile.user.last_name, 'Mokoena')
        self.assertFalse(profile.user.has_usable_password())
        self.assertFalse(profile.user.is_staff)


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_page_is_helpful_and_not_indexed(self):
        response = self.client.get('/a-page-that-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'This page could not be found.', status_code=404)
        self.assertContains(response, 'noindex, nofollow', status_code=404)
        self.assertContains(response, reverse('core:contact'), status_code=404)


class DetailPageDesignTests(TestCase):
    def test_article_practice_area_and_person_details_render(self):
        article = Article.objects.create(
            title='Legal update',
            slug='legal-update',
            excerpt='A concise legal update.',
            content='<p>Useful information.</p>',
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        area = PracticeArea.objects.create(
            name='Commercial law',
            slug='commercial-law',
            short_description='Commercial guidance for growing organisations.',
            description='<p>Commercial law overview.</p>',
        )
        user = get_user_model().objects.create_user(
            email='lawyer@example.com',
            first_name='Lerato',
            last_name='Mokoena',
        )
        person = Attorney.objects.create(
            user=user,
            title='Associate',
            slug='lerato-mokoena',
            biography='<p>Experienced legal professional.</p>',
        )
        person.practice_areas.add(area)

        article_response = self.client.get(article.get_absolute_url())
        area_response = self.client.get(area.get_absolute_url())
        person_response = self.client.get(person.get_absolute_url())

        self.assertContains(article_response, 'Important note')
        self.assertContains(area_response, 'Discuss your matter')
        self.assertContains(area_response, 'People in this area')
        self.assertContains(person_response, 'Areas of focus')
        self.assertContains(person_response, 'Meet more of our people', count=0)

# Create your tests here.
