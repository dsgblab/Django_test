from django.urls import path
from . import views
from .views import dashboard


urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('table1/', views.table1_list, name='table1_list'),
    path('table1/create/', views.table1_create, name='table1_create'),
    path('table1/delete/<int:pk>/', views.table1_delete, name='table1_delete'),

    path('table2/', views.table2_list, name='table2_list'),
    path('table2/create/', views.table2_create, name='table2_create'),
    path('table2/delete/<int:pk>/', views.table2_delete, name='table2_delete'),

    
]
