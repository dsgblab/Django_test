from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views
from .views import dashboard, query_result_view

urlpatterns = [
    path('', dashboard, name='dashboard'),

    # Table 1
    path('table1/', views.table1_list, name='table1_list'),
    path('table1/create/', views.table1_create, name='table1_create'),
    path('table1/delete/<int:pk>/', views.table1_delete, name='table1_delete'),
    path('table1/edit/<int:pk>/', views.table1_edit, name='table1_edit'),

    # Table 2
    path('table2/', views.table2_list, name='table2_list'),
    path('table2/create/', views.table2_create, name='table2_create'),
    path('table2/delete/<int:pk>/', views.table2_delete, name='table2_delete'),    
    path('table2/edit/<int:pk>/', views.table2_edit, name='table2_edit'),

    # Reportes
    path('query/', query_result_view, name='query_result'),  
    path('query-report/', views.query_report_view, name='query_report_view'),
    path('reporte-historico/', views.historial_pvo_view, name='historial_pvo'), 

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # PVO CRUD
    path('pvo/', views.pvo_list, name='pvo_list'),
    path('pvo/create/', views.pvo_create, name='pvo_create'),
    path('pvo/edit/<str:pk>/', views.pvo_edit, name='pvo_edit'),

    # path('editar-fechas/<str:pid>/', views.editar_fechas_pvo, name='editar_fechas_pvo'),

    path('actualizar-fecha/<str:pid>/<str:campo>/', views.actualizar_fecha, name='actualizar_fecha'),

]
