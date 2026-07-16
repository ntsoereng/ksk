from django.views.generic import DetailView, ListView
from .models import Attorney


class AttorneyListView(ListView):
    queryset = Attorney.objects.filter(is_active=True).select_related('user').prefetch_related('practice_areas')
    template_name = 'attorneys/list.html'
    context_object_name = 'attorneys'


class AttorneyDetailView(DetailView):
    queryset = Attorney.objects.filter(is_active=True).select_related('user').prefetch_related('practice_areas')
    template_name = 'attorneys/detail.html'
    context_object_name = 'attorney'
