from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultas', '0002_pacienteconta'),
    ]

    operations = [
        migrations.AddField(
            model_name='consulta',
            name='preferencial',
            field=models.BooleanField(default=False),
        ),
    ]
