from django import forms
from reservaciones.models import Reservacion


class ReservacionForm(forms.ModelForm):
    class Meta:
        model = Reservacion
        fields = [
            'sala',
            'fecha',
            'hora_inicio',
            'hora_fin',
            'asistentes',
            'proposito',
        ]
