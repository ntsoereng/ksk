from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from .rate_limits import client_address, consume_limit


class SearchIndexingMiddleware(MiddlewareMixin):
    """Keep private routes and failed requests out of search results."""

    def process_response(self, request, response):
        if request.path.startswith(('/staff/', '/admin/')) or response.status_code >= 400:
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response


class FormProtectionMiddleware(MiddlewareMixin):
    """Limit writes before invoking authentication or content handlers."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != 'POST':
            return None
        name = request.resolver_match.view_name
        rules = []
        if name == 'core:contact':
            rules.append(('contact_ip', client_address(request)))
            email = request.POST.get('email', '').strip().casefold()
            if email:
                rules.append(('contact_email', email))
        elif name in {'core:staff_login', 'admin:login'}:
            rules.append(('login_ip', client_address(request)))
            account = request.POST.get('username', '').strip().casefold()
            if account:
                rules.append(('login_account', account))
        elif name not in {'core:staff_logout', 'admin:logout'} and request.user.is_authenticated and request.user.is_staff and request.path.startswith((reverse('core:staff_dashboard'), reverse('admin:index'))):
            scope = 'upload_user' if name == 'core:staff_content_image_upload' else 'staff_user'
            rules.append((scope, str(request.user.pk)))

        for scope, identity in rules:
            retry_after = consume_limit(scope, identity)
            if retry_after:
                if name == 'core:staff_content_image_upload':
                    response = JsonResponse({'error': 'Too many uploads. Please wait before trying again.'}, status=429)
                else:
                    response = render(request, '429.html', {
                        'retry_minutes': max(1, (retry_after + 59) // 60),
                        'return_url': request.path,
                    }, status=429)
                response['Retry-After'] = str(retry_after)
                response['Cache-Control'] = 'no-store'
                return response
        return None
