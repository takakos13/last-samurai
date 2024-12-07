# Generated by Django 5.1.3 on 2024-12-02 12:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_favoritefacility'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapedEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(max_length=200)),
                ('event_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('location', models.CharField(max_length=200)),
                ('organizer', models.CharField(max_length=200)),
                ('event_url', models.URLField(max_length=500)),
                ('event_class', models.CharField(max_length=100)),
                ('event_category', models.CharField(max_length=100)),
                ('total_capacity', models.CharField(max_length=50)),
                ('participants', models.CharField(max_length=50)),
                ('spots_left', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['event_date', 'start_time'],
            },
        ),
        migrations.AlterModelOptions(
            name='reservation',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='event',
            name='category',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='event',
            name='level_class',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.event'),
        ),
    ]
