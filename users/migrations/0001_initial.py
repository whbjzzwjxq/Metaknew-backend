# Generated by Django 2.2 on 2019-09-10 11:30

import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore
import django.core.validators
from django.db import migrations, models
import tools.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAuthority',
            fields=[
                ('SourceId', models.BigIntegerField(db_index=True, primary_key=True, serialize=False)),
                ('Used', models.BooleanField(db_column='used', default=True)),
                ('Common', models.BooleanField(db_column='common', default=True)),
                ('Shared', models.BooleanField(db_column='shared', default=False)),
                ('OpenSource', models.BooleanField(db_column='open', default=False)),
                ('Payment', models.BooleanField(db_column='payment', default=False)),
                ('Vip', models.BooleanField(db_column='vip', default=False)),
                ('HighVip', models.BooleanField(db_column='high_vip', default=False)),
            ],
            options={
                'db_table': 'graph_authority_course',
            },
        ),
        migrations.CreateModel(
            name='DocAuthority',
            fields=[
                ('SourceId', models.BigIntegerField(db_index=True, primary_key=True, serialize=False)),
                ('Used', models.BooleanField(db_column='used', default=True)),
                ('Common', models.BooleanField(db_column='common', default=True)),
                ('Shared', models.BooleanField(db_column='shared', default=False)),
                ('OpenSource', models.BooleanField(db_column='open', default=False)),
                ('Payment', models.BooleanField(db_column='payment', default=False)),
                ('Vip', models.BooleanField(db_column='vip', default=False)),
                ('HighVip', models.BooleanField(db_column='high_vip', default=False)),
            ],
            options={
                'db_table': 'graph_authority_doc',
            },
        ),
        migrations.CreateModel(
            name='GroupCtrl',
            fields=[
                ('GroupId', models.BigIntegerField(db_column='Group_Id', primary_key=True, serialize=False)),
                ('GroupName', models.TextField(db_column='Group_Name', unique=True)),
                ('CreateUser', models.BigIntegerField(db_column='Create_User')),
                ('Owner', models.BigIntegerField(db_column='Owner')),
                ('Manager', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Manager', size=None)),
                ('Member', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Member', size=None)),
                ('Topic', tools.models.TopicField(base_field=models.TextField(), db_index=True, default=list, size=None)),
                ('Labels', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=list, size=None)),
                ('Is_Auto', models.BooleanField(db_column='Auto', default=False)),
                ('Is_Open', models.BooleanField(db_column='Open', default=True)),
            ],
            options={
                'db_table': 'user_info_base_group',
            },
        ),
        migrations.CreateModel(
            name='MediaAuthority',
            fields=[
                ('SourceId', models.BigIntegerField(db_index=True, primary_key=True, serialize=False)),
                ('Used', models.BooleanField(db_column='used', default=True)),
                ('Common', models.BooleanField(db_column='common', default=True)),
                ('Shared', models.BooleanField(db_column='shared', default=False)),
                ('OpenSource', models.BooleanField(db_column='open', default=False)),
                ('Payment', models.BooleanField(db_column='payment', default=False)),
                ('Vip', models.BooleanField(db_column='vip', default=False)),
                ('HighVip', models.BooleanField(db_column='high_vip', default=False)),
            ],
            options={
                'db_table': 'graph_authority_media',
            },
        ),
        migrations.CreateModel(
            name='NodeAuthority',
            fields=[
                ('SourceId', models.BigIntegerField(db_index=True, primary_key=True, serialize=False)),
                ('Used', models.BooleanField(db_column='used', default=True)),
                ('Common', models.BooleanField(db_column='common', default=True)),
                ('Shared', models.BooleanField(db_column='shared', default=False)),
                ('OpenSource', models.BooleanField(db_column='open', default=False)),
                ('Payment', models.BooleanField(db_column='payment', default=False)),
                ('Vip', models.BooleanField(db_column='vip', default=False)),
                ('HighVip', models.BooleanField(db_column='high_vip', default=False)),
            ],
            options={
                'db_table': 'graph_authority_node',
            },
        ),
        migrations.CreateModel(
            name='Privilege',
            fields=[
                ('UserId', models.BigIntegerField(db_index=True, primary_key=True, serialize=False)),
                ('Is_Owner', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Owner', default=list, size=None)),
                ('Is_Manager', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Manager', default=list, size=None)),
                ('Is_Collaborator', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Coll', default=list, size=None)),
                ('Is_SharedTo', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='ShareTo', default=list, size=None)),
                ('Is_FreeTo', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='FreeTo', default=list, size=None)),
                ('Is_Paid', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), db_column='Paid', default=list, size=None)),
            ],
            options={
                'db_table': 'user_authority_count',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('UserId', models.BigIntegerField(db_column='USER_ID', primary_key=True, serialize=False)),
                ('UserName', models.TextField(db_column='USER_NAME', unique=True)),
                ('UserPw', models.TextField(db_column='USER_PASSWORD')),
                ('UserEmail', models.TextField(db_column='USER_EMAIL')),
                ('UserPhone', models.CharField(db_column='USER_PHONE', max_length=11, unique=True)),
                ('DateTime', models.DateTimeField(auto_now_add=True, db_column='USER_TIME')),
                ('Is_Superuser', models.BooleanField(db_column='ROOT', default=False)),
                ('Is_Developer', models.BooleanField(db_column='DEV', default=False)),
                ('Is_Publisher', models.BooleanField(db_column='PUBLISH', default=False)),
                ('Is_Vip', models.BooleanField(db_column='VIP', default=False)),
                ('Is_high_vip', models.BooleanField(db_column='HighVIP', default=False)),
                ('Is_Active', models.BooleanField(db_column='Active', default=True)),
                ('Is_Banned', models.BooleanField(db_column='Banned', default=False)),
                ('Joint_Group', django.contrib.postgres.fields.hstore.HStoreField(db_column='JOINT_GROUP', default=dict)),
            ],
            options={
                'db_table': 'user_info_base',
            },
        ),
        migrations.CreateModel(
            name='UserConcern',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UserId', models.BigIntegerField(db_index=True)),
                ('SourceId', models.BigIntegerField(db_index=True)),
                ('SourceType', models.TextField(db_index=True)),
                ('Labels', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=list, size=None)),
                ('Imp', tools.models.LevelField(default=-1, validators=[django.core.validators.MinValueValidator(limit_value=-1), django.core.validators.MaxValueValidator(limit_value=100)])),
                ('HardLevel', tools.models.LevelField(default=-1, validators=[django.core.validators.MinValueValidator(limit_value=-1), django.core.validators.MaxValueValidator(limit_value=100)])),
                ('Useful', tools.models.LevelField(default=-1, validators=[django.core.validators.MinValueValidator(limit_value=-1), django.core.validators.MaxValueValidator(limit_value=100)])),
                ('Is_Star', models.BooleanField(default=False)),
                ('Is_Tag', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'user_info_concern',
            },
        ),
        migrations.CreateModel(
            name='UserDocProgress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UserId', models.BigIntegerField(db_column='UserId', db_index=True)),
                ('SourceId', models.BigIntegerField(db_column='SourceId', db_index=True)),
                ('SourceType', models.TextField(db_column='SourceType', db_index=True)),
                ('SpendTime', models.IntegerField(db_column='SpendTime')),
                ('LastPart', models.BigIntegerField(db_column='LastPart')),
            ],
            options={
                'db_table': 'user_info_progress',
            },
        ),
        migrations.CreateModel(
            name='UserRepository',
            fields=[
                ('UserId', models.IntegerField(primary_key=True, serialize=False)),
                ('CreateDoc', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None)),
                ('CreateNode', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None)),
                ('CreateCourse', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None)),
                ('UploadFile', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None)),
                ('Fragment', django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None)),
            ],
            options={
                'db_table': 'user_info_collection',
            },
        ),
        migrations.AddIndex(
            model_name='userconcern',
            index=models.Index(fields=['SourceId', 'SourceType'], name='user_info_c_SourceI_60d106_idx'),
        ),
    ]
