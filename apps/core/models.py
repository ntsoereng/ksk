from django.db import models
from django.urls import reverse
from django.utils import timezone
from apps.articles.sanitizers import sanitize_rich_text


class Inquiry(models.Model):
    """A non-confidential request for an initial consultation."""

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'consultation inquiry'
        verbose_name_plural = 'consultation inquiries'

    def __str__(self):
        return f'{self.subject} — {self.name}'


class CaseStudy(models.Model):
    """An anonymised example of the firm's work, managed by staff."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=220)
    slug = models.SlugField(unique=True)
    client_label = models.CharField(
        max_length=140,
        blank=True,
        help_text='Use a generic description and never identify a client without written consent.',
    )
    summary = models.TextField(max_length=500)
    challenge = models.TextField()
    approach = models.TextField()
    outcome = models.TextField()
    featured_image = models.ImageField(upload_to='case-studies/', blank=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')
        verbose_name_plural = 'case studies'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:case_study_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.challenge = sanitize_rich_text(self.challenge)
        self.approach = sanitize_rich_text(self.approach)
        self.outcome = sanitize_rich_text(self.outcome)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class SiteInformation(models.Model):
    """The single editable source of truth for public website content."""

    firm_name = models.CharField(max_length=150, default='Khoboko Law Chambers')
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/branding/', blank=True)
    favicon = models.ImageField(upload_to='site/branding/', blank=True)
    site_url = models.URLField(
        blank=True,
        help_text='Public website URL, for example https://khobokolaw.co.ls (no trailing slash).',
    )
    seo_title = models.CharField(
        max_length=70,
        blank=True,
        help_text='Default search result title. Aim for 50–60 characters.',
    )
    seo_description = models.CharField(
        max_length=170,
        blank=True,
        help_text='Default search description. Aim for 140–160 characters.',
    )
    social_image = models.ImageField(
        upload_to='site/social/',
        blank=True,
        help_text='Default sharing image; a 1200 × 630 image works best.',
    )

    primary_phone = models.CharField(max_length=40, blank=True)
    secondary_phone = models.CharField(max_length=40, blank=True)
    primary_email = models.EmailField(blank=True)
    physical_address = models.TextField(blank=True)
    postal_address = models.CharField(max_length=255, blank=True)
    business_hours = models.CharField(max_length=255, blank=True)
    google_maps_url = models.URLField(blank=True)

    hero_title = models.CharField(max_length=255, default='Guiding you through the moments that matter.')
    hero_text = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to='site/hero/', blank=True)
    hero_cta_label = models.CharField(max_length=80, default='Request a consultation')
    practice_section_title = models.CharField(max_length=160, default='Legal services for life and business.')
    practice_section_text = models.TextField(blank=True)
    people_section_title = models.CharField(max_length=160, default='Counsel you can know and trust.')
    people_section_text = models.TextField(blank=True)
    home_cta_title = models.CharField(max_length=180, default='Talk to a legal team that listens first.')
    home_cta_text = models.TextField(blank=True)

    about_title = models.CharField(max_length=200, default='A firm grounded in service and integrity.')
    about_text = models.TextField(blank=True)
    mission_statement = models.TextField(blank=True)
    people_page_title = models.CharField(max_length=200, default='Experienced counsel. Personal attention.')
    people_page_text = models.TextField(blank=True)
    lawyers_section_intro = models.TextField(blank=True)
    staff_section_intro = models.TextField(blank=True)
    contact_title = models.CharField(max_length=180, default='Start a conversation.')
    contact_intro = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)
    terms_of_use = models.TextField(blank=True)
    legal_disclaimer = models.TextField(blank=True)

    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'site information'
        verbose_name_plural = 'site information'

    def __str__(self):
        return self.firm_name

    def save(self, *args, **kwargs):
        """Keep this model to a single record for predictable template usage."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        return cls.objects.filter(pk=1).first()
