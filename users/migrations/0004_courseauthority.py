# Generated by Django 2.2 on 2019-08-31 22:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20190829_1817'),
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
            ],
            options={
                'db_table': 'authority_course',
            },
        ),
    ]
