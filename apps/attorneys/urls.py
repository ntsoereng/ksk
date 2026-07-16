from django.urls import path
from .views import AttorneyDetailView, AttorneyListView

app_name = 'attorneys'

urlpatterns = [
    path('', AttorneyListView.as_view(), name='list'),
    path('<slug:slug>/', AttorneyDetailView.as_view(), name='detail'),
]
