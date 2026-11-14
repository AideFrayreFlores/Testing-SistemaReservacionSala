from django.db import migrations

SALAS = [
    ('Sala A', 4, 'Biblioteca, planta baja', True),
    ('Sala B', 8, 'Biblioteca, planta baja', True),
    ('Sala C', 12, 'Biblioteca, planta alta', True),
    ('Sala de mantenimiento', 6, 'Biblioteca, planta alta', False),
]


def crear_salas(apps, schema_editor):
    Sala = apps.get_model('salas', 'Sala')
    for nombre, capacidad, ubicacion, activa in SALAS:
        Sala.objects.create(
            nombre=nombre,
            capacidad=capacidad,
            ubicacion=ubicacion,
            activa=activa
        )


class Migration(migrations.Migration):

    dependencies = [('salas', '0001_initial')]

    operations = [
        migrations.RunPython(crear_salas, migrations.RunPython.noop)
    ]
