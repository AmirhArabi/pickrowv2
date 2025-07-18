# Generated by Django 4.2.3 on 2025-04-07 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminSidebar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Admin Sidebar',
                'verbose_name_plural': 'Admin Sidebar',
            },
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='browser',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='country_short',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='device_family',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='device_type',
            field=models.CharField(editable=False, max_length=50),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='is_mobile',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='is_pc',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='is_tablet',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='location',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='os',
            field=models.CharField(max_length=100),
        ),
    ]
