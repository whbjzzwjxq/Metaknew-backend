# Generated by Django 2.2 on 2019-10-20 23:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subgraph', '0003_auto_20191021_0526'),
    ]

    operations = [
        migrations.RenameField(
            model_name='knowledge',
            old_name='Selection',
            new_name='SelectTimes',
        ),
    ]
