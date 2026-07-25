from django.utils import timezone
from django.views.generic import DetailView, ListView
from .models import Article


class ArticleListView(ListView):
    template_name = 'articles/list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Article.objects.filter(status=Article.Status.PUBLISHED, published_at__lte=timezone.now()).select_related('author')


class ArticleDetailView(DetailView):
    template_name = 'articles/detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(status=Article.Status.PUBLISHED, published_at__lte=timezone.now()).select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_articles'] = self.get_queryset().exclude(
            pk=self.object.pk,
        )[:3]
        return context
