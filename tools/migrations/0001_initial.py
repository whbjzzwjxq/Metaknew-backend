# Generated by Django 2.2 on 2019-08-15 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceBlockIdRecord',
            fields=[
                ('BlockId', models.IntegerField(db_column='BLOCK_ID', db_index=True)),
                ('OutId', models.BigIntegerField(db_column='OUT_ID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'device_device_block',
            },
        ),
        migrations.CreateModel(
            name='DeviceBlockManager',
            fields=[
                ('BlockId', models.AutoField(db_column='BlockId', primary_key=True, serialize=False)),
                ('Classifier', models.IntegerField(db_column='LabelContent', db_index=True)),
                ('RegisterTime', models.DateTimeField(auto_now_add=True, db_column='RegisterTime')),
            ],
            options={
                'db_table': 'global_device_block_manager',
            },
        ),
        migrations.CreateModel(
            name='GlobalWordIndex',
            fields=[
                ('WordIndex', models.AutoField(db_column='Index', primary_key=True, serialize=False)),
                ('Word', models.TextField(db_column='Word', db_index=True, editable=False, unique=True)),
            ],
            options={
                'db_table': 'global_word_index',
            },
        ),
        migrations.CreateModel(
            name='NodeBlockIdRecord',
            fields=[
                ('BlockId', models.IntegerField(db_column='BLOCK_ID', db_index=True)),
                ('OutId', models.BigIntegerField(db_column='OUT_ID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'device_node_block',
            },
        ),
        migrations.CreateModel(
            name='NodeBlockManager',
            fields=[
                ('BlockId', models.AutoField(db_column='BlockId', primary_key=True, serialize=False)),
                ('Classifier', models.IntegerField(db_column='LabelContent', db_index=True)),
                ('RegisterTime', models.DateTimeField(auto_now_add=True, db_column='RegisterTime')),
            ],
            options={
                'db_table': 'global_node_block_manager',
            },
        ),
        migrations.CreateModel(
            name='RecordBlockIdRecord',
            fields=[
                ('BlockId', models.IntegerField(db_column='BLOCK_ID', db_index=True)),
                ('OutId', models.BigIntegerField(db_column='OUT_ID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'device_time_block',
            },
        ),
        migrations.CreateModel(
            name='RecordBlockManager',
            fields=[
                ('BlockId', models.AutoField(db_column='BlockId', primary_key=True, serialize=False)),
                ('Classifier', models.IntegerField(db_column='LabelContent', db_index=True)),
                ('RegisterTime', models.DateTimeField(auto_now_add=True, db_column='RegisterTime')),
            ],
            options={
                'db_table': 'global_private_block_manager',
            },
        ),
    ]
