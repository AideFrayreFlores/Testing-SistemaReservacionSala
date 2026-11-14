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
        return cleaned_data
