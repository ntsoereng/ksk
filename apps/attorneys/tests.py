from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Attorney


class PeopleDirectoryTests(TestCase):
    def make_person(self, email, first_name, member_type, display_order):
        user = get_user_model().objects.create_user(
            email=email,
            first_name=first_name,
            last_name='Test',
        )
        return Attorney.objects.create(
            user=user,
            title='Team member',
            member_type=member_type,
            slug=first_name.lower(),
            biography='Profile biography.',
            display_order=display_order,
        )

    def test_legal_professionals_are_separate_and_listed_first(self):
        staff = self.make_person(
            'staff@example.com', 'Staff', Attorney.MemberType.STAFF, 0,
        )
        lawyer = self.make_person(
            'lawyer@example.com', 'Lawyer', Attorney.MemberType.LAWYER, 20,
        )

        response = self.client.get(reverse('attorneys:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['lawyers'], [lawyer])
        self.assertEqual(response.context['staff_members'], [staff])
        self.assertLess(
            response.content.index(b'Lawyer Test'),
            response.content.index(b'Staff Test'),
        )

    def test_inactive_people_are_not_public(self):
        person = self.make_person(
            'inactive@example.com', 'Inactive', Attorney.MemberType.LAWYER, 0,
        )
        person.is_active = False
        person.save()

        response = self.client.get(reverse('attorneys:list'))

        self.assertNotContains(response, 'Inactive Test')
