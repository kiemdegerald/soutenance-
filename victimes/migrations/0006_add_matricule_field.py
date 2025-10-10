# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('victimes', '0005_remove_fichevictime_matricule'),
    ]

    operations = [
        migrations.AddField(
            model_name='fichevictime',
            name='matricule',
            field=models.CharField(default='', max_length=50, verbose_name='Matricule'),
        ),
    ]