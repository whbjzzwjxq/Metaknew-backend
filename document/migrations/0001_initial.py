# Generated by Django 2.2 on 2019-09-10 11:30

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import document.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('CommentId', models.BigIntegerField(db_column='ID', primary_key=True, serialize=False)),
                ('SourceId', models.BigIntegerField(db_column='Source', db_index=True)),
                ('TargetId', models.BigIntegerField(db_column='TARGET', db_index=True)),
                ('TargetUser', models.BigIntegerField(db_column='TARGET_USER', db_index=True)),
                ('Content', models.TextField(db_column='CONTENT', default='')),
                ('Owner', models.BigIntegerField(db_column='USER', db_index=True, default='0')),
                ('CreateTime', models.DateTimeField(auto_now_add=True, db_column='TIME')),
                ('Is_Delete', models.BooleanField(db_column='DELETED', default=False)),
            ],
            options={
                'db_table': 'document_comment',
            },
        ),
        migrations.CreateModel(
            name='DocGraph',
            fields=[
                ('DocId', models.BigIntegerField(editable=False, primary_key=True, serialize=False)),
                ('Nodes', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), db_column='Nodes', default=document.models.node_setting, size=None)),
                ('Links', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), db_column='Relationships', default=document.models.link_setting, size=None)),
                ('CommonNotes', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), db_column='Notes', default=document.models.note_setting, size=None)),
                ('Conf', django.contrib.postgres.fields.jsonb.JSONField(db_column='CONF', default=document.models.graph_setting)),
            ],
            options={
                'db_table': 'document_graph',
            },
        ),
        migrations.CreateModel(
            name='DocPaper',
            fields=[
                ('DocId', models.BigIntegerField(editable=False, primary_key=True, serialize=False)),
                ('Nodes', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), db_column='Nodes', default=document.models.card_setting, size=None)),
                ('CommonNotes', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), db_column='Notes', default=document.models.note_setting, size=None)),
                ('Conf', django.contrib.postgres.fields.jsonb.JSONField(default=document.models.paper_setting)),
            ],
            options={
                'db_table': 'document_paper',
            },
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('NoteId', models.BigIntegerField(primary_key=True, serialize=False)),
                ('CreateUser', models.IntegerField(db_column='UserId', db_index=True, default='1')),
                ('DocumentId', models.BigIntegerField(db_column='DocumentId')),
                ('TagType', models.TextField(db_column='TagsType', default='normal')),
                ('Content', models.TextField(db_column='Content', default='')),
                ('Conf', django.contrib.postgres.fields.jsonb.JSONField(db_column='Configure')),
                ('Is_Open', models.BooleanField(db_index=True, default=False)),
                ('Is_Delete', models.BooleanField(db_index=True, default=False)),
            ],
            options={
                'db_table': 'document_note',
            },
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['CreateUser', 'DocumentId', 'Is_Delete'], name='document_no_UserId_3fe920_idx'),
        ),
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['CreateUser'], name='document_no_UserId_2f2acb_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['SourceId', 'Is_Delete'], name='Count_DocComment'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['TargetUser', 'Is_Delete'], name='Count_ReplyComment'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['Owner', 'Is_Delete'], name='Count_OwnerComment'),
        ),
    ]
