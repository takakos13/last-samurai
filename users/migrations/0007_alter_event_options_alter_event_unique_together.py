# Generated by Django 5.1.4 on 2024-12-07 07:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_scrapedevent_event_url_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['event_date', 'start_time']},
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together={('event_name', 'event_date', 'start_time', 'facility')},
        ),
    ]
