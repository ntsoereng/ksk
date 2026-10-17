from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse


class RichTextSanitizer(HTMLParser):
    """Keep the limited, safe HTML produced by the staff article editor."""

    allowed_tags = {'p', 'br', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote', 'a', 'img', 'figure', 'figcaption'}
    void_tags = {'br', 'img'}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.allowed_tags:
            return
        if tag == 'img':
            attributes = dict(attrs)
            src = attributes.get('src') or ''
            try:
                parsed = urlparse(src)
                valid = (
                    (parsed.scheme in {'https', 'http'} and bool(parsed.netloc))
                    or (src.startswith('/') and not src.startswith('//'))
                ) and not any(ord(char) < 32 or char == chr(92) for char in src)
            except ValueError:
                valid = False
            if valid:
                alt = attributes.get('alt') or ''
                self.parts.append(
                    f'<img src="{escape(src, quote=True)}" alt="{escape(alt, quote=True)}" loading="lazy" decoding="async">'
                )
            return
        if tag == 'a':
            href = dict(attrs).get('href', '')
            parsed = urlparse(href)
            if parsed.scheme not in {'http', 'https', 'mailto'}:
                href = ''
            self.parts.append(f'<a href="{escape(href, quote=True)}" rel="noopener noreferrer">')
            return
        self.parts.append(f'<{tag}>')

    def handle_startendtag(self, tag, attrs):
        if tag in self.void_tags:
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.allowed_tags and tag not in self.void_tags:
            self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(escape(data))


def sanitize_rich_text(value):
    sanitizer = RichTextSanitizer()
    sanitizer.feed(value or '')
    sanitizer.close()
    return ''.join(sanitizer.parts)
