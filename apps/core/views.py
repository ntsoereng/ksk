from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.attorneys.models import Attorney
from apps.practice_areas.models import PracticeArea
from .forms import InquiryForm

def home(request):
    context = {
        'featured_practice_areas': PracticeArea.objects.filter(is_active=True, is_featured=True)[:3],
        'featured_attorneys': Attorney.objects.filter(is_active=True).select_related('user')[:3],
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
