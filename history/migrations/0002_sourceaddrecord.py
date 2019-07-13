# Generated by Django 2.2 on 2019-07-13 06:31

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceAddRecord',
            fields=[
                ('id', models.AutoField(db_column='ID', primary_key=True, serialize=False)),
                ('Is_Error', models.BooleanField(db_column='ERROR', default=False)),
                ('Is_Warn', models.BooleanField(db_column='WARN', default=False)),
                ('SourceId', models.UUIDField(db_column='UUID')),
                ('SourceType', models.TextField(db_column='TYPE')),
                ('Content', django.contrib.postgres.fields.jsonb.JSONField(db_column='CONTENT', default=dict)),
                ('Time', models.DateTimeField(auto_now_add=True, db_column='TIME')),
            ],
            options={
                'db_table': 'source_add_record',
            },
        ),
    ]