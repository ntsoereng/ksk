from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('case-studies/', views.case_study_list, name='case_study_list'),
    path('case-studies/<slug:slug>/', views.case_study_detail, name='case_study_detail'),
    path('staff/login/', views.StaffLoginView.as_view(), name='staff_login'),
    path('staff/logout/', LogoutView.as_view(next_page='core:home'), name='staff_logout'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/content/<slug:section>/', views.staff_content_list, name='staff_content_list'),
    path('staff/content/<slug:section>/new/', views.staff_content_edit, name='staff_content_add'),
    path('staff/content/<slug:section>/images/', views.staff_content_image_upload, name='staff_content_image_upload'),
    path('staff/content/<slug:section>/<int:pk>/edit/', views.staff_content_edit, name='staff_content_edit'),
    path('staff/content/<slug:section>/<int:pk>/delete/', views.staff_content_delete, name='staff_content_delete'),
    path('staff/site-settings/', views.staff_site_settings, name='staff_site_settings'),
    path('staff/messages/', views.staff_messages, name='staff_messages'),
    path('staff/messages/<int:pk>/', views.staff_message_detail, name='staff_message_detail'),
]
