from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from django.shortcuts import redirect, render
from django.http import FileResponse, Http404, HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.staticfiles import finders
import mimetypes
from django.views.decorators.http import require_http_methods

from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea
from apps.articles.models import Article
from .forms import InquiryForm
from .models import CaseStudy, Inquiry, SiteInformation
from .staff_forms import (
    ArticleStaffForm,
    AttorneyStaffForm,
    CaseStudyStaffForm,
    PracticeAreaStaffForm,
    SiteInformationStaffForm,
)


STAFF_CONTENT = {
    'posts': {
        'model': Article,
        'form': ArticleStaffForm,
        'title': 'Posts',
        'singular': 'post',
        'permission_app': 'articles',
        'permission_model': 'article',
    },
    'practice-areas': {
        'model': PracticeArea,
        'form': PracticeAreaStaffForm,
        'title': 'Practice areas',
        'singular': 'practice area',
        'permission_app': 'practice_areas',
        'permission_model': 'practicearea',
    },
    'case-studies': {
        'model': CaseStudy,
        'form': CaseStudyStaffForm,
        'title': 'Case studies',
        'singular': 'case study',
        'permission_app': 'core',
        'permission_model': 'casestudy',
    },
    'people': {
        'model': Attorney,
        'form': AttorneyStaffForm,
        'title': 'People',
        'singular': 'profile',
        'permission_app': 'attorneys',
        'permission_model': 'attorney',
    },
}


def _content_config(section):
    config = STAFF_CONTENT.get(section)
    if not config:
        raise PermissionDenied
    return config


def _require_content_permission(request, config, action):
    permission = (
        f"{config['permission_app']}.{action}_{config['permission_model']}"
    )
    if not request.user.has_perm(permission):
        raise PermissionDenied


class StaffLoginView(LoginView):
    template_name = 'core/staff_login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            logout(request)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.get_redirect_url() or reverse('core:staff_dashboard')

    def form_valid(self, form):
        if not form.get_user().is_staff:
            form.add_error(None, 'This portal is available to authorised staff only.')
            return self.form_invalid(form)
        return super().form_valid(form)

def home(request):
    featured_people = Attorney.objects.filter(
        is_active=True,
        is_featured=True,
        member_type=Attorney.MemberType.LAWYER,
    ).select_related('user')[:3]
    if not featured_people.exists():
        featured_people = Attorney.objects.filter(
            is_active=True,
            member_type=Attorney.MemberType.LAWYER,
        ).select_related('user')[:3]
    context = {
        'featured_practice_areas': PracticeArea.objects.filter(is_active=True, is_featured=True)[:3],
        'featured_attorneys': featured_people,
    }
    return render(request, 'core/home.html', context)


@require_http_methods(['GET', 'POST'])
def contact(request):
    form = InquiryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thank you. Our team will be in touch shortly.')
        return redirect('core:contact')
    return render(request, 'core/contact.html', {'form': form})


def about(request):
    return render(request, 'core/about.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def terms(request):
    return render(request, 'core/terms.html')


def case_study_list(request):
    studies = CaseStudy.objects.filter(
        status=CaseStudy.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    return render(request, 'core/case_study_list.html', {
        'case_studies': studies,
    })


def case_study_detail(request, slug):
    study = get_object_or_404(
        CaseStudy,
        slug=slug,
        status=CaseStudy.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    related_studies = CaseStudy.objects.filter(
        status=CaseStudy.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    ).exclude(pk=study.pk)[:3]
    return render(request, 'core/case_study_detail.html', {
        'case_study': study,
        'related_case_studies': related_studies,
    })


@staff_member_required(login_url='core:staff_login')
def staff_dashboard(request):
    context = {
        'content_counts': {
            'articles': Article.objects.count(),
            'practice_areas': PracticeArea.objects.count(),
            'case_studies': CaseStudy.objects.count(),
            'people': Attorney.objects.count(),
            'unread_messages': Inquiry.objects.filter(is_read=False).count(),
        },
        'recent_messages': Inquiry.objects.order_by('-created_at')[:6],
        'recent_articles': Article.objects.select_related('author').order_by('-updated_at')[:5],
        'recent_case_studies': CaseStudy.objects.order_by('-updated_at')[:5],
    }
    return render(request, 'core/staff_dashboard.html', context)


@staff_member_required(login_url='core:staff_login')
def staff_content_list(request, section):
    config = _content_config(section)
    _require_content_permission(request, config, 'view')
    objects = config['model'].objects.all()
    if section == 'posts':
        objects = objects.select_related('author')
    elif section == 'people':
        objects = objects.select_related('user')
    return render(request, 'core/staff_content_list.html', {
        'section': section,
        'content_config': config,
        'objects': objects,
        'can_add': request.user.has_perm(
            f"{config['permission_app']}.add_{config['permission_model']}"
        ),
        'can_change': request.user.has_perm(
            f"{config['permission_app']}.change_{config['permission_model']}"
        ),
        'can_delete': request.user.has_perm(
            f"{config['permission_app']}.delete_{config['permission_model']}"
        ),
    })


@staff_member_required(login_url='core:staff_login')
def staff_content_edit(request, section, pk=None):
    config = _content_config(section)
    action = 'change' if pk else 'add'
    _require_content_permission(request, config, action)
    instance = get_object_or_404(config['model'], pk=pk) if pk else None
    form = config['form'](
        request.POST or None,
        request.FILES or None,
        instance=instance,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            obj = form.save(commit=False)
            if section == 'posts' and obj.author_id is None:
                obj.author = request.user
            obj.save()
            form.save_m2m()
        messages.success(
            request,
            f"{config['singular'].capitalize()} saved successfully.",
        )
        return redirect('core:staff_content_list', section=section)
    return render(request, 'core/staff_content_form.html', {
        'section': section,
        'content_config': config,
        'form': form,
        'object': instance,
    })


@staff_member_required(login_url='core:staff_login')
def staff_content_delete(request, section, pk):
    config = _content_config(section)
    _require_content_permission(request, config, 'delete')
    obj = get_object_or_404(config['model'], pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(
            request,
            f"{config['singular'].capitalize()} deleted.",
        )
        return redirect('core:staff_content_list', section=section)
    return render(request, 'core/staff_content_confirm_delete.html', {
        'section': section,
        'content_config': config,
        'object': obj,
    })


@staff_member_required(login_url='core:staff_login')
def staff_site_settings(request):
    if not request.user.has_perm('core.change_siteinformation'):
        raise PermissionDenied
    information = SiteInformation.get_solo() or SiteInformation(pk=1)
    form = SiteInformationStaffForm(
        request.POST or None,
        request.FILES or None,
        instance=information,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Site settings saved successfully.')
        return redirect('core:staff_site_settings')
    return render(request, 'core/staff_content_form.html', {
        'content_config': {
            'title': 'Site settings',
            'singular': 'site settings',
        },
        'form': form,
        'object': information if information.pk else None,
        'is_site_settings': True,
    })


@staff_member_required(login_url='core:staff_login')
def staff_messages(request):
    if not request.user.has_perm('core.view_inquiry'):
        raise PermissionDenied
    return render(request, 'core/staff_messages.html', {
        'inquiries': Inquiry.objects.all(),
        'unread_count': Inquiry.objects.filter(is_read=False).count(),
    })


@staff_member_required(login_url='core:staff_login')
def staff_message_detail(request, pk):
    if not request.user.has_perm('core.view_inquiry'):
        raise PermissionDenied
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        if not request.user.has_perm('core.change_inquiry'):
            raise PermissionDenied
        inquiry.is_read = not inquiry.is_read
        inquiry.save(update_fields=('is_read',))
        messages.success(request, 'Message status updated.')
        return redirect('core:staff_message_detail', pk=inquiry.pk)
    return render(request, 'core/staff_message_detail.html', {
        'inquiry': inquiry,
    })


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    content = f'User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {sitemap_url}\n'
    return HttpResponse(content, content_type='text/plain')


def favicon(request):
    """Stream the favicon without depending on media/static URL mappings."""
    information = SiteInformation.get_solo()
    if information and information.favicon:
        try:
            filename = information.favicon.name
            file_handle = information.favicon.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404('Configured favicon file was not found.')
    else:
        filename = finders.find('images/branding/favicon.svg')
        if not filename:
            raise Http404('Fallback favicon was not found.')
        file_handle = open(filename, 'rb')
    content_type = mimetypes.guess_type(str(filename))[0] or 'image/x-icon'
    response = FileResponse(file_handle, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=3600, must-revalidate'
    return response


def media_file(request, path):
    """Stream a stored upload when Apache/Passenger forwards /media to Django."""
    try:
        if not default_storage.exists(path):
            raise Http404('Media file was not found.')
        file_handle = default_storage.open(path, 'rb')
    except (FileNotFoundError, OSError, SuspiciousFileOperation):
        raise Http404('Media file was not found.')
    content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    response = FileResponse(file_handle, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=86400'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
