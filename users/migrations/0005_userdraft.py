# Generated by Django 2.2 on 2019-10-24 00:48

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_delete_userdraft'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDraft',
            fields=[
                ('RecordId', models.AutoField(primary_key=True, serialize=False)),
                ('UserId', models.BigIntegerField(db_column='UserId', db_index=True)),
                ('SourceId', models.BigIntegerField(db_column='SourceId', db_index=True)),
                ('SourceType', models.TextField(db_column='SourceType', db_index=True)),
                ('UpdateTime', models.DateField(auto_now=True, db_column='UpdateTime')),
                ('Content', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('DontClear', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'user_draft',
            },
        ),
    ]
