# Generated by Django 2.2 on 2019-09-10 14:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nodeversionrecord',
            name='BaseHistory',
        ),
    ]
