from datetime import date, time
from django import forms
from reservaciones.models import Reservacion


class ReservacionForm(forms.ModelForm):
    asistentes = forms.IntegerField(min_value=1)
    proposito = forms.CharField(
        max_length=200,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'El propósito debe tener entre 10 y 200 caracteres.',
        }
    )

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

    def clean_proposito(self):
        proposito = self.cleaned_data.get('proposito', '').strip()
        if len(proposito) < 10:
            raise forms.ValidationError(
                'El propósito debe tener entre 10 y 200 caracteres.'
            )
        return proposito

    def clean(self):
        cleaned_data = super().clean()
        sala = cleaned_data.get('sala')
        asistentes = cleaned_data.get('asistentes')
        if sala and asistentes is not None and asistentes > sala.capacidad:
            self.add_error(
                'asistentes',
                'El número de asistentes supera la capacidad de la sala.'
            )
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error(
                'hora_fin',
                'La hora de fin debe ser posterior a la hora de inicio.'
            )
        return cleaned_data

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < date.today():
            raise forms.ValidationError(
                'La fecha no puede ser anterior al día actual.'
            )
        return fecha

    def clean_hora_inicio(self):
        hora_inicio = self.cleaned_data.get('hora_inicio')
        if hora_inicio and (
            hora_inicio < time(8, 0) or hora_inicio > time(19, 0)
        ):
            raise forms.ValidationError(
                'La hora de inicio debe encontrarse entre 08:00 y 19:00.'
            )
        return hora_inicio

    def clean_hora_fin(self):
        hora_fin = self.cleaned_data.get('hora_fin')
        if hora_fin and hora_fin > time(20, 0):
            raise forms.ValidationError(
                'La hora de fin no puede exceder las 20:00.'
            )
        return hora_fin

    def clean_sala(self):
        sala = self.cleaned_data.get('sala')
        if sala and not sala.activa:
            raise forms.ValidationError(
                'La sala no se encuentra disponible para reservación.'
            )
        return sala
