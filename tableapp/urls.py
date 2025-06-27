from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views
from .views import dashboard, query_result_view

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('table1/', views.table1_list, name='table1_list'),
    path('table1/create/', views.table1_create, name='table1_create'),
    path('table1/delete/<int:pk>/', views.table1_delete, name='table1_delete'),
    path('table1/edit/<int:pk>/', views.table1_edit, name='table1_edit'),

    path('table2/', views.table2_list, name='table2_list'),
    path('table2/create/', views.table2_create, name='table2_create'),
    path('table2/delete/<int:pk>/', views.table2_delete, name='table2_delete'),    
    path('table2/edit/<int:pk>/', views.table2_edit, name='table2_edit'),


    path('query/', query_result_view, name='query_result'),  
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  
]
