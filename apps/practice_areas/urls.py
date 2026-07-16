from django.urls import path
from .views import PracticeAreaDetailView, PracticeAreaListView

app_name = 'practice_areas'

urlpatterns = [
    path('', PracticeAreaListView.as_view(), name='list'),
    path('<slug:slug>/', PracticeAreaDetailView.as_view(), name='detail'),
]
