# Generated by Django 3.0.3 on 2020-03-01 18:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0002_auto_20200227_1832'),
    ]

    operations = [
        migrations.RenameField(
            model_name='docgraph',
            old_name='Svgs',
            new_name='Texts',
        ),
    ]
