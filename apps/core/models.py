from django.db import models


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


class SiteInformation(models.Model):
    """The single editable source of truth for public website content."""

    firm_name = models.CharField(max_length=150, default='Khoboko Law Chambers')
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/branding/', blank=True)
    favicon = models.ImageField(upload_to='site/branding/', blank=True)

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

    about_title = models.CharField(max_length=200, default='A firm grounded in service and integrity.')
    about_text = models.TextField(blank=True)
    mission_statement = models.TextField(blank=True)

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
