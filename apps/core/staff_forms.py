from django import forms
from django.contrib.auth import get_user_model

from apps.articles.forms import RichTextWidget
from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea

from .models import CaseStudy, SiteInformation


class StaffModelForm(forms.ModelForm):
    """Consistent, accessible styling for staff-facing content forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.ClearableFileInput)):
                continue
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} staff-form-control'.strip()


class ArticleStaffForm(StaffModelForm):
    class Meta:
        model = Article
        fields = ('title', 'slug', 'excerpt', 'content', 'featured_image',
                  'status', 'is_featured', 'published_at')
        widgets = {
            'content': RichTextWidget(),
            'published_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }


class PracticeAreaStaffForm(StaffModelForm):
    class Meta:
        model = PracticeArea
        fields = ('name', 'slug', 'short_description', 'description',
                  'is_featured', 'display_order', 'is_active')
        widgets = {'description': RichTextWidget()}


class CaseStudyStaffForm(StaffModelForm):
    class Meta:
        model = CaseStudy
        fields = ('title', 'slug', 'client_label', 'summary', 'challenge',
                  'approach', 'outcome', 'featured_image', 'status',
                  'is_featured', 'published_at')
        widgets = {
            'challenge': RichTextWidget(),
            'approach': RichTextWidget(),
            'outcome': RichTextWidget(),
            'published_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }


class AttorneyStaffForm(StaffModelForm):
    class Meta:
        model = Attorney
        fields = ('user', 'title', 'member_type', 'slug', 'biography', 'photo',
                  'admission', 'email', 'phone', 'practice_areas',
                  'display_order', 'is_featured', 'is_active')
        widgets = {
            'biography': RichTextWidget(),
            'practice_areas': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available_users = get_user_model().objects.filter(is_active=True)
        if self.instance and self.instance.pk:
            available_users = available_users.filter(
                attorney_profile__isnull=True,
            ) | available_users.filter(pk=self.instance.user_id)
        else:
            available_users = available_users.filter(attorney_profile__isnull=True)
        self.fields['user'].queryset = available_users.distinct().order_by(
            'first_name', 'last_name', 'email',
        )


class SiteInformationStaffForm(StaffModelForm):
    class Meta:
        model = SiteInformation
        exclude = ('updated_at',)
