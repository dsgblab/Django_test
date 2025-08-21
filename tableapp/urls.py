from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views
from .views import dashboard

urlpatterns = [
    path('', dashboard, name='dashboard'),

    # Reportes 
    path('query-report/', views.query_report_view, name='query_report_view'), 

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # PVO CRUD
    path('pvo/', views.pvo_list, name='pvo_list'),
    path('pvo/create/', views.pvo_create, name='pvo_create'),
    path('pvo/edit/<str:pk>/', views.pvo_edit, name='pvo_edit'),

    # Actualizar fechas (HTMX)
    path('actualizar-fecha/<str:pid>/<str:campo>/', views.actualizar_fecha, name='actualizar_fecha'),

    # Historial modal
    path('pvo/historial/<str:pid>/', views.pvo_historial_modal, name='pvo_historial_modal'),

    # <<< NUEVO: endpoint para actualizar config FP por código de producto >>>
    path('actualizar-fp/<str:codigo_producto>/<str:campo>/', views.actualizar_fp, name='actualizar_fp'),
]
