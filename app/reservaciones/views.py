from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from reservaciones.forms import ReservacionForm


@login_required
def nueva_reservacion(request):
    form = ReservacionForm()
    return render(
        request,
        'reservaciones/nueva_reservacion.html',
        {'form': form}
    )
