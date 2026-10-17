from django import forms
from django.contrib.auth import get_user_model

from apps.articles.forms import RichTextWidget
from apps.articles.models import Article
from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea

from .models import CaseStudy, SiteInformation
from .forms import GoogleMapsEmbedField


class StaffModelForm(forms.ModelForm):
    """Consistent, accessible styling for staff-facing content forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, RichTextWidget):
                widget.upload_section = {
                    Article: 'posts', CaseStudy: 'case-studies',
                    PracticeArea: 'practice-areas', Attorney: 'people',
                }.get(self._meta.model, 'posts')
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
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    person_email = forms.EmailField(
        label='Email address',
        help_text='Used for this profile. Creating a profile does not grant staff-portal access.',
    )

    class Meta:
        model = Attorney
        fields = ('first_name', 'last_name', 'person_email',
                  'title', 'member_type', 'slug', 'biography', 'photo',
                  'admission', 'email', 'phone', 'practice_areas',
                  'display_order', 'is_featured', 'is_active')
        widgets = {
            'biography': RichTextWidget(),
            'practice_areas': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['person_email'].initial = self.instance.user.email

    def clean_person_email(self):
        email = get_user_model().objects.normalize_email(
            self.cleaned_data['person_email'],
        )
        users = get_user_model().objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            users = users.exclude(pk=self.instance.user_id)
        if users.exists():
            raise forms.ValidationError(
                'This email address is already attached to another account or profile.',
            )
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.pk:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['person_email']
            user.save(update_fields=('first_name', 'last_name', 'email'))
        else:
            user = get_user_model().objects.create_user(
                email=self.cleaned_data['person_email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
            )
            profile.user = user
        if commit:
            profile.save()
            self.save_m2m()
        return profile


class SiteInformationStaffForm(StaffModelForm):
    google_maps_embed_url = GoogleMapsEmbedField()

    class Meta:
        model = SiteInformation
        exclude = ('updated_at',)
