# Generated by Django 2.2 on 2019-10-24 00:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userdraft_dontclear'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserDraft',
        ),
    ]
