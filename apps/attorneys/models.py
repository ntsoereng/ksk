from django.conf import settings
from django.db import models
from django.urls import reverse
from apps.articles.sanitizers import sanitize_rich_text


class Attorney(models.Model):
    class MemberType(models.TextChoices):
        LAWYER = 'lawyer', 'Legal professional'
        STAFF = 'staff', 'Professional & support staff'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attorney_profile')
    title = models.CharField(
        max_length=100, help_text='For example: Managing Partner, Associate, Office Manager or Intern.')
    member_type = models.CharField(
        max_length=10,
        choices=MemberType,
        default=MemberType.LAWYER,
        help_text='Legal professionals are always listed before general staff.',
    )
    slug = models.SlugField(unique=True)
    biography = models.TextField()
    photo = models.ImageField(upload_to='attorneys/', blank=True)
    admission = models.CharField(
        max_length=200, blank=True, help_text='Court admission or professional designation.')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    practice_areas = models.ManyToManyField(
        'practice_areas.PracticeArea', blank=True, related_name='attorneys')
    display_order = models.PositiveSmallIntegerField(default=0)
    is_featured = models.BooleanField(
        default=False,
        help_text='Feature this person on the homepage. Legal professionals are prioritised.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('member_type', 'display_order', 'user__last_name', 'user__first_name')

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    @property
    def display_email(self):
        return self.email or self.user.email

    def get_absolute_url(self):
        return reverse('attorneys:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.biography = sanitize_rich_text(self.biography)
        super().save(*args, **kwargs)

    @property
    def is_lawyer(self):
        return self.member_type == self.MemberType.LAWYER
