from datetime import date
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
