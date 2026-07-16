from django.views.generic import DetailView, ListView
from .models import PracticeArea


class PracticeAreaListView(ListView):
    queryset = PracticeArea.objects.filter(is_active=True)
    template_name = 'practice_areas/list.html'
    context_object_name = 'practice_areas'


class PracticeAreaDetailView(DetailView):
    queryset = PracticeArea.objects.filter(is_active=True)
    template_name = 'practice_areas/detail.html'
    context_object_name = 'practice_area'
