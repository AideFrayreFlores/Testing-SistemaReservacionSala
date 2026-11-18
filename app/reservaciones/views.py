from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion
from reservaciones.services import (
    cancelar_reservacion as cancelar_reservacion_servicio,
)
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
    error_servicio = None
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
            try:
                reservacion = registrar_reservacion(datos)
                messages.success(
                    request,
                    f'Reservación registrada exitosamente. '
                    f'Sala: {reservacion.sala.nombre}, '
                    f'Fecha: {reservacion.fecha}, '
                    f'Horario: {reservacion.hora_inicio.strftime("%H:%M")} a '
                    f'{reservacion.hora_fin.strftime("%H:%M")}.'
                )
                return redirect('lista_reservaciones')
            except ValidationError as error:
                error_servicio = error.messages[0]
    else:
        form = ReservacionForm()
    return render(
        request,
        'reservaciones/nueva_reservacion.html',
        {'form': form, 'error_servicio': error_servicio}
    )


@login_required
@require_POST
def cancelar_reservacion(request, reservacion_id):
    try:
        cancelar_reservacion_servicio(reservacion_id, request.user)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, 'Reservación cancelada exitosamente.')
    return redirect('lista_reservaciones')
