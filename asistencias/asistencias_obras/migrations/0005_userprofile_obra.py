# Generated by Django 2.2.12 on 2024-03-09 01:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('asistencias_obras', '0004_auto_20240309_0018'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='obra',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='asistencias_obras.Obra'),
        ),
    ]
