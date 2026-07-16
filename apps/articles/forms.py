from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .models import Article


class RichTextWidget(forms.Textarea):
    class Media:
        js = ('js/rich-text-editor.js',)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        textarea = super().render(name, value, attrs, renderer)
        editor_id = f'{attrs.get("id", name)}_editor'
        content = mark_safe(value or '')
        return format_html(
            '<div class="rich-text-widget" data-textarea-id="{textarea_id}">'
            '<div class="rich-text-toolbar" role="toolbar" aria-label="Article formatting">'
            '<button type="button" data-command="bold"><strong>B</strong></button>'
            '<button type="button" data-command="italic"><em>I</em></button>'
            '<button type="button" data-command="formatBlock" data-value="h2">Heading</button>'
            '<button type="button" data-command="insertUnorderedList">• List</button>'
            '<button type="button" data-command="insertOrderedList">1. List</button>'
            '<button type="button" data-command="createLink">Link</button>'
            '</div><div id="{editor_id}" class="rich-text-editor" contenteditable="true">{content}</div>{textarea}</div>',
            textarea_id=attrs.get('id', name), editor_id=editor_id, content=content, textarea=mark_safe(textarea),
        )


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {'content': RichTextWidget(attrs={'class': 'rich-text-source'})}
