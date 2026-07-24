from django.db import models
from django.urls import reverse
from apps.articles.sanitizers import sanitize_rich_text


class PracticeArea(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=220)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True,
                            help_text='An optional icon identifier for the website.')
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('display_order', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.description = sanitize_rich_text(self.description)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('practice_areas:detail', kwargs={'slug': self.slug})
