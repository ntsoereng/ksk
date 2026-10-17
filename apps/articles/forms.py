from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse

from .models import Article
from .sanitizers import sanitize_rich_text


class RichTextWidget(forms.Textarea):
    upload_section = 'posts'

    class Media:
        js = ('js/rich-text-editor.js',)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        textarea = super().render(name, value, attrs, renderer)
        editor_id = f'{attrs.get("id", name)}_editor'
        content = mark_safe(sanitize_rich_text(value or ''))
        return format_html(
            '<div class="rich-text-widget" data-textarea-id="{textarea_id}" data-upload-url="{upload_url}">'
            '<div class="rich-text-toolbar" role="group" aria-label="Content formatting">'
            '<button type="button" data-command="bold"><strong>B</strong></button>'
            '<button type="button" data-command="italic"><em>I</em></button>'
            '<button type="button" data-command="formatBlock" data-value="h2">Heading</button>'
            '<button type="button" data-command="insertUnorderedList">• List</button>'
            '<button type="button" data-command="insertOrderedList">1. List</button>'
            '<button type="button" data-command="createLink">Link</button>'
            '<button type="button" data-image-toggle aria-expanded="false" aria-controls="{editor_id}_images">Image</button>'
            '</div><div id="{editor_id}_images" class="rich-text-image-panel" hidden>'
            '<label for="{editor_id}_file">Upload an image (JPEG, PNG or WebP; up to 8 MB)</label>'
            '<input id="{editor_id}_file" type="file" accept="image/jpeg,image/png,image/webp" data-image-file>'
            '<label for="{editor_id}_url">Or use an image URL</label>'
            '<input id="{editor_id}_url" type="url" placeholder="https://…" data-image-url>'
            '<label for="{editor_id}_alt">Image description (alt text)</label>'
            '<input id="{editor_id}_alt" type="text" data-image-alt>'
            '<label for="{editor_id}_caption">Caption (optional)</label>'
            '<input id="{editor_id}_caption" type="text" data-image-caption>'
            '<button type="button" class="button-primary mt-3" data-image-insert>Insert image</button>'
            '<p class="rich-text-status mt-2" role="status" aria-live="polite"></p>'
            '</div><div id="{editor_id}" class="rich-text-editor" contenteditable="true" role="textbox" aria-multiline="true" aria-label="{field_name} content">{content}</div>{textarea}</div>',
            textarea_id=attrs.get('id', name), editor_id=editor_id, content=content, textarea=mark_safe(textarea),
            upload_url=reverse('core:staff_content_image_upload', args=(self.upload_section,)),
            field_name=name.replace('_', ' ').capitalize(),
        )


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {'content': RichTextWidget(attrs={'class': 'rich-text-source'})}
