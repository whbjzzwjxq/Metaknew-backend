# Generated by Django 2.2 on 2019-08-16 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subgraph', '0002_auto_20190816_0359'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basedoc',
            name='Keywords',
        ),
        migrations.RemoveField(
            model_name='basedoc',
            name='TotalTime',
        ),
        migrations.AddField(
            model_name='basedoc',
            name='Size',
            field=models.IntegerField(db_column='Size', default=1),
        ),
        migrations.AddField(
            model_name='medianode',
            name='TotalTime',
            field=models.IntegerField(db_column='TotalTime', default=50),
        ),
        migrations.AddField(
            model_name='nodectrl',
            name='TotalTime',
            field=models.IntegerField(db_column='TotalTime', default=50),
        ),
    ]