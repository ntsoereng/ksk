from django.views.generic import DetailView, ListView
from .models import Attorney


class AttorneyListView(ListView):
    queryset = Attorney.objects.filter(is_active=True).select_related('user').prefetch_related('practice_areas')
    template_name = 'attorneys/list.html'
    context_object_name = 'attorneys'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        people = context['attorneys']
        context['lawyers'] = [person for person in people if person.is_lawyer]
        context['staff_members'] = [person for person in people if not person.is_lawyer]
        return context


class AttorneyDetailView(DetailView):
    queryset = Attorney.objects.filter(is_active=True).select_related('user').prefetch_related('practice_areas')
    template_name = 'attorneys/detail.html'
    context_object_name = 'attorney'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_people'] = Attorney.objects.filter(
            is_active=True,
            member_type=self.object.member_type,
        ).exclude(pk=self.object.pk).select_related('user')[:3]
        return context
