# Generated by Django 2.2 on 2019-10-24 00:40

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDraft',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UserId', models.BigIntegerField(db_column='UserId', db_index=True)),
                ('SourceId', models.BigIntegerField(db_column='SourceId', db_index=True)),
                ('SourceType', models.TextField(db_column='SourceType', db_index=True)),
                ('UpdateTime', models.DateField(auto_now=True, db_column='UpdateTime')),
                ('Content', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            options={
                'db_table': 'user_draft',
            },
        ),
    ]
