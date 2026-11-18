from django.urls import path
from reservaciones import views

urlpatterns = [
    path('', views.listar_reservaciones, name='lista_reservaciones'),
    path('nueva', views.crear_reservacion, name='nueva_reservacion'),
    path(
        'cancelar/<int:reservacion_id>',
        views.cancelar_reservacion,
        name='cancelar_reservacion'
    ),
]
