# Generated by Django 4.2.15 on 2025-03-29 07:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cartitem',
            options={'ordering': ['id'], 'verbose_name_plural': '03. Cart Items'},
        ),
    ]
