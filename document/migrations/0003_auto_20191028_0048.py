# Generated by Django 2.2 on 2019-10-27 16:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0002_auto_20191027_2330'),
    ]

    operations = [
        migrations.RenameField(
            model_name='docpaper',
            old_name='Paths',
            new_name='Path',
        ),
        migrations.RenameField(
            model_name='graphversionrecord',
            old_name='Paths',
            new_name='Path',
        ),
    ]
