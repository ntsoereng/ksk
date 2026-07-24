from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.articles.models import Article

from .models import Inquiry, SiteInformation


class SeoTests(TestCase):
    def test_pages_have_canonical_metadata_and_fallback_favicon(self):
        response = self.client.get(reverse('core:home'))

        self.assertContains(response, '<link rel="canonical"', html=False)
        self.assertContains(response, 'favicon.svg')
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


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_page_is_helpful_and_not_indexed(self):
        response = self.client.get('/a-page-that-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'This page could not be found.', status_code=404)
        self.assertContains(response, 'noindex, nofollow', status_code=404)
        self.assertContains(response, reverse('core:contact'), status_code=404)

# Create your tests here.
