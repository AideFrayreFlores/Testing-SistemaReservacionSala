from django import forms
from reservaciones.models import Reservacion


class ReservacionForm(forms.ModelForm):
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
