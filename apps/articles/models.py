from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .sanitizers import sanitize_rich_text


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=220)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(max_length=350, help_text='A concise summary for article listings.')
    content = models.TextField(help_text='Use the editor toolbar to format the article body.')
    featured_image = models.ImageField(upload_to='articles/', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='articles')
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.content = sanitize_rich_text(self.content)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'slug': self.slug})
