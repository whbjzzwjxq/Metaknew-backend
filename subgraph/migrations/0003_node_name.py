# Generated by Django 2.2 on 2019-07-06 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subgraph', '0002_auto_20190706_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='Name',
            field=models.TextField(db_column='NAME', default=''),
            preserve_default=False,
        ),
    ]