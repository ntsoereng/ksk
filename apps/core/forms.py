from django import forms
from html.parser import HTMLParser
from .models import Inquiry, SiteInformation
from .validators import validate_google_maps_embed_url


class MapIframeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.src = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'iframe':
            self.src = dict(attrs).get('src', '')


class GoogleMapsEmbedField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(required=False, label='Google Maps embed',
                         widget=forms.Textarea(attrs={'rows': 3}),
                         help_text=SiteInformation._meta.get_field('google_maps_embed_url').help_text,
                         **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value.startswith('<'):
            parser = MapIframeParser()
            parser.feed(value)
            value = parser.src
            if not value:
                raise forms.ValidationError('The iframe must contain a Google Maps embed src URL.')
        validate_google_maps_embed_url(value)
        return value


class SiteInformationAdminForm(forms.ModelForm):
    google_maps_embed_url = GoogleMapsEmbedField()

    class Meta:
        model = SiteInformation
        fields = '__all__'


class InquiryForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Briefly describe the type of assistance you need. Please omit confidential details.'}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('website'):
            raise forms.ValidationError('We could not accept this enquiry. Please try again or contact the chambers directly.')
        return cleaned

    class Meta:
        model = Inquiry
        fields = ('name', 'email', 'phone', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel', 'placeholder': 'Your contact number'}),
            'subject': forms.TextInput(attrs={'placeholder': 'What would you like to discuss?'}),
        }
