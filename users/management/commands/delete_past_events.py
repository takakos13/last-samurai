from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import Event, Reservation
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Q

class Command(BaseCommand):
    help = '開催日時が過ぎたイベントを削除します（予約があるものは除く）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-datetime',
            type=str,
            help='テスト用の日時を指定 (形式: YYYY-MM-DD HH:MM)',
        )

    def handle(self, *args, **options):
        if options['test_datetime']:
            try:
                test_datetime = datetime.strptime(options['test_datetime'], '%Y-%m-%d %H:%M')
                current_datetime = make_aware(test_datetime)
                self.stdout.write(f'Using test datetime: {current_datetime}')
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid datetime format. Use YYYY-MM-DD HH:MM')
                )
                return
        else:
            current_datetime = timezone.now()

        reserved_event_ids = Reservation.objects.filter(
            event__isnull=False
        ).values_list('event_id', flat=True)

        past_events_condition = Q(event_date__lt=current_datetime.date()) | Q(
            event_date=current_datetime.date(),
            start_time__lt=current_datetime.time()
        )

        events_to_delete = Event.objects.filter(
            past_events_condition
        ).exclude(
            id__in=reserved_event_ids
        ).order_by('event_date', 'start_time')

        total_events = events_to_delete.count()
        events_deleted = 0

        for event in events_to_delete:
            try:
                event.delete()
                events_deleted += 1
            except Exception:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {events_deleted} out of {total_events} past events (Based on: {current_datetime})'
            )
        ) 