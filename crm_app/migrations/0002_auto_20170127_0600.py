# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-01-27 06:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='msgreports',
            name='status',
            field=models.CharField(blank=True, choices=[('1', '1'), ('2', '2'), ('16', '16')], max_length=250, null=True),
        ),
    ]