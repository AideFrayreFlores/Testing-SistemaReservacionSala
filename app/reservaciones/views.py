from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion
from reservaciones.services import registrar_reservacion


@login_required
def listar_reservaciones(request):
    reservaciones = Reservacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha', '-hora_inicio')
    return render(
        request,
        'reservaciones/lista_reservaciones.html',
        {'reservaciones': reservaciones}
    )


@login_required
def crear_reservacion(request):
    if request.method == 'POST':
        form = ReservacionForm(request.POST)
        if form.is_valid():
            datos = {
                'usuario': request.user,
                'sala': form.cleaned_data['sala'],
                'fecha': form.cleaned_data['fecha'],
                'hora_inicio': form.cleaned_data['hora_inicio'],
                'hora_fin': form.cleaned_data['hora_fin'],
                'asistentes': form.cleaned_data['asistentes'],
                'proposito': form.cleaned_data['proposito'],
            }
            reservacion = registrar_reservacion(datos)
            messages.success(
                request,
                f'Reservación registrada exitosamente. Sala: {reservacion.sala.nombre}, '
                f'Fecha: {reservacion.fecha}, '
                f'Horario: {reservacion.hora_inicio.strftime("%H:%M")} a '
                f'{reservacion.hora_fin.strftime("%H:%M")}.'
            )
            return redirect('lista_reservaciones')
    else:
        form = ReservacionForm()
    return render(
        request,
        'reservaciones/nueva_reservacion.html',
        {'form': form}
    )
