from django.urls import path
from reservaciones import views

urlpatterns = [
    path('nueva', views.nueva_reservacion, name='nueva_reservacion'),
]
