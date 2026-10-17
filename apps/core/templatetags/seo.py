import json
from html import unescape

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

from apps.core.seo import absolute_url, public_origin

register = template.Library()


def plain_text(value, length=170):
    return Truncator(' '.join(unescape(strip_tags(str(value))).split())).chars(length)


@register.simple_tag(takes_context=True)
def page_metadata(context):
    request = context['request']
    info = context['site_information']
    origin = public_origin(request, info)
    name = info.firm_name or 'Khoboko Law Chambers'
    route = request.resolver_match.view_name if request.resolver_match else ''
    pages = {
        'core:about': ('About us', f'Learn about {name}, our approach to legal services in Lesotho and our commitment to clear, practical counsel.'),
        'core:contact': ('Contact', f'Contact {name} in Lesotho to discuss your legal matter, request a consultation or find our office and contact details.'),
        'core:privacy': ('Privacy policy', f'How {name} handles website enquiries, personal information, essential cookies and privacy requests.'),
        'core:terms': ('Terms of use', f'Terms for using the {name} website, including legal information, enquiries, confidentiality and acceptable use.'),
        'core:case_study_list': ('Case studies', f'Explore selected examples of how {name} approaches legal matters with care and practical judgement.'),
        'practice_areas:list': ('Practice areas', f'Explore legal services and practice areas at {name} for individuals, families and businesses in Lesotho.'),
        'attorneys:list': ('Our people', f'Meet the legal professionals and support staff at {name} in Lesotho.'),
        'articles:list': ('Legal insights', f'Legal insights, practical guidance and updates from the team at {name} in Lesotho.'),
    }
    label, description = pages.get(route, (
        '', info.seo_description or info.tagline or
        'Clear, trusted legal counsel for individuals, families and businesses in Lesotho.',
    ))
    image = info.social_image or info.logo
    firm_image_url = absolute_url(origin, image.url if image else static('images/branding/social-preview.png'))
    image_alt = name
    kind = 'website'
    entity = None
    parent = None
    if article := context.get('article'):
        label, description = article.title, article.excerpt
        image = article.featured_image or image
        image_alt = article.title if article.featured_image else name
        kind = 'article'
        parent = ('articles:list', 'Legal insights')
        entity = {
            '@type': 'BlogPosting', 'headline': article.title,
            'datePublished': article.published_at.isoformat(),
            'dateModified': article.updated_at.isoformat(),
            'publisher': {'@id': f'{origin}/#firm'},
        }
        if article.author:
            author_name = article.author.get_full_name()
            if author_name:
                entity['author'] = {'@type': 'Person', 'name': author_name}
    elif study := context.get('case_study'):
        label, description = study.title, study.summary
        image = study.featured_image or image
        image_alt = study.title if study.featured_image else name
        parent = ('core:case_study_list', 'Case studies')
        entity = {'@type': 'CreativeWork', 'name': study.title,
                  'datePublished': study.published_at.isoformat(),
                  'dateModified': study.updated_at.isoformat()}
    elif person := context.get('attorney'):
        label = str(person)
        description = f'{person}, {person.title} at {name}. {person.biography}'
        image = person.photo or image
        image_alt = str(person) if person.photo else name
        parent = ('attorneys:list', 'Our people')
        entity = {'@type': 'Person', 'name': str(person), 'jobTitle': person.title,
                  'worksFor': {'@id': f'{origin}/#firm'}}
    elif area := context.get('practice_area'):
        label, description = area.name, area.short_description
        parent = ('practice_areas:list', 'Practice areas')
        entity = {'@type': 'Service', 'name': area.name,
                  'provider': {'@id': f'{origin}/#firm'}, 'areaServed': 'Lesotho'}
    title = f'{label} | {name}' if label else (info.seo_title or f'{name} | Legal counsel in Lesotho')
    description = plain_text(description)
    canonical = context['canonical_url']
    image_url = absolute_url(origin, image.url if image else static('images/branding/social-preview.png'))
    firm = {'@type': 'LegalService', '@id': f'{origin}/#firm',
            'name': name, 'url': f'{origin}/', 'image': firm_image_url,
            'areaServed': {'@type': 'Country', 'name': 'Lesotho'}}
    if info.logo:
        firm['logo'] = absolute_url(origin, info.logo.url)
    for field, value in [('telephone', info.primary_phone), ('email', info.primary_email)]:
        if value:
            firm[field] = value
    if info.physical_address:
        firm['address'] = {'@type': 'PostalAddress', 'streetAddress': info.physical_address, 'addressCountry': 'LS'}
    socials = [info.facebook_url, info.linkedin_url, info.instagram_url]
    if any(socials):
        firm['sameAs'] = list(filter(None, socials))
    page_types = {'core:about': 'AboutPage', 'core:contact': 'ContactPage',
                  'attorneys:detail': 'ProfilePage'}
    page = {'@type': page_types.get(route, 'WebPage'), '@id': f'{canonical}#webpage',
            'url': canonical, 'name': title, 'description': description,
            'isPartOf': {'@id': f'{origin}/#website'}, 'inLanguage': 'en'}
    graph = [firm, {'@type': 'WebSite', '@id': f'{origin}/#website',
                    'url': f'{origin}/', 'name': name, 'publisher': {'@id': f'{origin}/#firm'}}, page]
    if entity:
        entity.update({'@id': f'{canonical}#entity', 'url': canonical,
                       'description': description, 'image': image_url})
        page['mainEntity'] = {'@id': entity['@id']}
        graph.append(entity)
    if label:
        crumbs = [('Home', f'{origin}/')]
        if parent:
            crumbs.append((parent[1], absolute_url(origin, reverse(parent[0]))))
        crumbs.append((label, canonical))
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': text, 'item': url}
            for i, (text, url) in enumerate(crumbs, 1)
        ]})
    # Escape script delimiters without escapejs, which does not produce JSON escapes.
    structured = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)
    structured = structured.replace('&', '\\u0026').replace('<', '\\u003C').replace('>', '\\u003E')
    return {'title': title, 'description': description, 'type': kind,
            'image': image_url, 'image_alt': plain_text(image_alt, 420),
            'structured_data': mark_safe(structured),
            'article': context.get('article')}
