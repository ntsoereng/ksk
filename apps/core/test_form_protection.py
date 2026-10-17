from datetime import timedelta
import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import InquiryForm
from .models import FormRateLimit, Inquiry, SiteInformation
from .rate_limits import client_address, consume_limit


LIMITS = {
    'contact_ip': (2, 900), 'contact_email': (2, 900),
    'login_ip': (2, 900), 'login_account': (2, 900),
    'upload_user': (2, 60), 'staff_user': (2, 60),
}


class ClientAddressTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(FORM_TRUSTED_PROXIES=[])
    def test_untrusted_peer_cannot_spoof_address(self):
        request = self.factory.post('/', REMOTE_ADDR='192.0.2.2', HTTP_X_FORWARDED_FOR='198.51.100.1')
        self.assertEqual(client_address(request), '192.0.2.2')

    @override_settings(FORM_TRUSTED_PROXIES=['10.0.0.0/8'])
    def test_trusted_chain_uses_last_untrusted_address(self):
        request = self.factory.post('/', REMOTE_ADDR='10.0.0.2', HTTP_X_FORWARDED_FOR='203.0.113.99, 198.51.100.2, 10.0.0.3')
        self.assertEqual(client_address(request), '198.51.100.2')
        request.META['HTTP_X_FORWARDED_FOR'] = 'invalid'
        self.assertEqual(client_address(request), '10.0.0.2')

    @override_settings(FORM_TRUSTED_PROXIES=[])
    def test_ipv6_is_normalized(self):
        request = self.factory.post('/', REMOTE_ADDR='2001:0db8:0:0:0:0:0:1')
        self.assertEqual(client_address(request), '2001:db8::1')


@override_settings(FORM_RATE_LIMITS=LIMITS)
class FormProtectionTests(TestCase):
    def enquiry(self, email='visitor@example.test', **extra):
        return self.client.post(reverse('core:contact'), {
            'name': 'Visitor', 'email': email, 'phone': '',
            'subject': 'Property advice', 'message': 'Please contact me about property advice.',
            **extra,
        })

    def test_contact_is_limited_across_sessions_and_spoofed_headers(self):
        self.assertEqual(self.enquiry().status_code, 302)
        self.assertEqual(self.enquiry().status_code, 302)
        self.client = Client(HTTP_X_FORWARDED_FOR='203.0.113.1')
        response = self.enquiry(email='another@example.test')
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response['Retry-After']), 0)
        self.assertLessEqual(int(response['Retry-After']), 900)
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertContains(response, 'not processed', status_code=429)
        self.assertEqual(Inquiry.objects.count(), 2)
        self.assertEqual(self.client.get(reverse('core:contact')).status_code, 200)

    def test_contact_email_limit_survives_changing_networks(self):
        self.enquiry()
        self.client = Client(REMOTE_ADDR='192.0.2.3')
        self.enquiry(email='VISITOR@example.test')
        self.client = Client(REMOTE_ADDR='192.0.2.4')
        self.assertEqual(self.enquiry().status_code, 429)
        self.assertEqual(Inquiry.objects.count(), 2)

    def test_invalid_submissions_count_and_honeypot_cannot_create_enquiry(self):
        response = self.enquiry(website='https://spam.example')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'could not accept this enquiry')
        self.assertEqual(Inquiry.objects.count(), 0)
        self.enquiry(email='invalid')
        self.assertEqual(self.enquiry().status_code, 429)

    def test_contact_message_has_length_limit(self):
        form = InquiryForm(data={
            'name': 'Visitor', 'email': 'visitor@example.test',
            'subject': 'Question', 'message': 'x' * 5001,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_contact_retains_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('core:contact'), {}).status_code, 403)
        self.assertEqual(FormRateLimit.objects.count(), 0)

    def test_both_login_endpoints_share_attempt_limits(self):
        for url in [reverse('core:staff_login'), reverse('admin:login')]:
            self.assertEqual(self.client.post(url, {'username': 'nobody@example.test', 'password': 'wrong'}).status_code, 200)
        response = self.client.post(reverse('core:staff_login'), {'username': 'other@example.test', 'password': 'wrong'})
        self.assertEqual(response.status_code, 429)
        self.assertNotContains(response, 'nobody@example.test', status_code=429)

    def test_login_account_limit_applies_across_networks(self):
        for address in ['192.0.2.3', '192.0.2.4']:
            client = Client(REMOTE_ADDR=address)
            self.assertEqual(client.post(reverse('core:staff_login'), {'username': 'Nobody@example.test', 'password': 'wrong'}).status_code, 200)
        response = self.client.post(reverse('admin:login'), {'username': 'nobody@example.test', 'password': 'wrong'})
        self.assertEqual(response.status_code, 429)

    def test_limits_expire_and_do_not_store_raw_identifiers(self):
        now = time.time()
        with patch('apps.core.rate_limits.time.time', return_value=now):
            self.assertEqual(consume_limit('contact_email', 'visitor@example.test'), 0)
            self.assertEqual(consume_limit('contact_email', 'visitor@example.test'), 0)
            self.assertGreater(consume_limit('contact_email', 'visitor@example.test'), 0)
        counter = FormRateLimit.objects.get()
        self.assertEqual(counter.count, 2)
        self.assertNotIn('visitor', counter.key)
        self.assertEqual(len(counter.key), 64)
        with patch('apps.core.rate_limits.time.time', return_value=now + 901):
            self.assertEqual(consume_limit('contact_email', 'visitor@example.test'), 0)

    def test_expired_counters_are_cleaned_up(self):
        FormRateLimit.objects.create(key='expired', expires_at=timezone.now() - timedelta(minutes=1))
        consume_limit('contact_ip', '192.0.2.1')
        self.assertFalse(FormRateLimit.objects.filter(key='expired').exists())

    def test_upload_limits_return_json_and_staff_writes_are_limited(self):
        staff = get_user_model().objects.create_superuser(email='limited@example.test', password='test-pass')
        self.client.force_login(staff)
        upload_url = reverse('core:staff_content_image_upload', args=('posts',))
        self.assertEqual(self.client.post(upload_url).status_code, 400)
        self.assertEqual(self.client.post(upload_url).status_code, 400)
        response = self.client.post(upload_url)
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.json())
        # Uploads have a separate allowance from ordinary content editing.
        write_url = reverse('core:staff_content_add', args=('posts',))
        self.assertEqual(self.client.post(write_url).status_code, 200)
        self.assertEqual(self.client.post(write_url).status_code, 200)
        self.assertEqual(self.client.post(write_url).status_code, 429)
        # A throttled editor can still sign out.
        self.assertEqual(self.client.post(reverse('core:staff_logout')).status_code, 302)

    def test_privacy_terms_and_contact_explain_the_current_features(self):
        response = self.client.get(reverse('core:contact'))
        self.assertContains(response, 'contact-icon')
        self.assertContains(response, 'name="website"')
        self.assertContains(response, reverse('core:privacy'))
        self.assertContains(response, reverse('core:terms'))
        privacy = self.client.get(reverse('core:privacy'))
        self.assertContains(privacy, 'Cookies, security counters and external content')
        self.assertContains(privacy, 'Your requests and concerns')
        terms = self.client.get(reverse('core:terms'))
        self.assertContains(terms, 'Enquiries and accepting instructions')
        self.assertContains(terms, 'Applicable law and changes')
        SiteInformation.objects.create(privacy_policy='Custom privacy policy', terms_of_use='Custom terms')
        self.assertContains(self.client.get(reverse('core:privacy')), 'Custom privacy policy')
        self.assertContains(self.client.get(reverse('core:terms')), 'Custom terms')
