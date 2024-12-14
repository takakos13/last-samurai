import argparse
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.utils.scraper import LaBolaScraper
from users.models import ScrapedEvent
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = '指定した条件で自動的にスクレイピングを実行します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--today',
            action='store_true',
            help='翌日ではなく当日の日付でスクレイピングを実行',
        )
        parser.add_argument('--date', help='検索日 (YYYY-MM-DD形式)')
        parser.add_argument('--time', help='検索終了時刻 (HH:MM形式)')
        parser.add_argument('--place', help='検索場所')

    def handle(self, *args, **options):
        try:
            if options['date'] and options['time'] and options['place']:
                target_datetime = datetime.strptime(f"{options['date']} {options['time']}", "%Y-%m-%d %H:%M")
                scraping_conditions = {
                    'location': options['place'],
                    'date': options['date'],
                    'start_time': options['time']
                }
            else:
                if options['today']:
                    target_date = timezone.now().strftime('%Y-%m-%d')
                else:
                    target_date = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                
                scraping_conditions = {
                    'location': '東京',
                    'date': target_date,
                    'start_time': '12:00'
                }
            
            self.stdout.write(
                self.style.SUCCESS(f'スクレイピング開始: {scraping_conditions}')
            )

            scraper = LaBolaScraper()
            scraped_events = scraper.search_events(
                date=scraping_conditions['date'],
                location=scraping_conditions['location'],
                start_time=scraping_conditions['start_time']
            )

            if scraped_events:
                for event_data in scraped_events:
                    try:
                        event_data['event_name'] = event_data.get('name', '')
                        
                        required_fields = ['event_name', 'date', 'time', 'location', 'organizer', 'url']
                        missing_fields = [field for field in required_fields if not event_data.get(field)]
                        
                        if missing_fields:
                            self.stdout.write(
                                self.style.WARNING(f'不足しているフィールド: {missing_fields}')
                            )
                            continue

                        scraped_event = ScrapedEvent(
                            event_name=event_data['event_name'],
                            event_date=datetime.strptime(event_data['date'], '%Y/%m/%d').date(),
                            start_time=datetime.strptime(event_data['time'], '%H:%M').time(),
                            location=event_data['location'],
                            organizer=event_data['organizer'],
                            event_url=event_data['url'],
                            event_class=event_data.get('class', ''),
                            event_category=event_data.get('category', ''),
                            total_capacity=event_data['capacity']['total'],
                            participants=event_data['capacity']['participants'],
                            spots_left=event_data['capacity']['remaining']
                        )
                        
                        scraped_event.save()
                        
                        scraped_event.convert_to_facility_and_event()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'イベントを保存しました: {event_data["event_name"]}')
                        )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'イベント保存エラー: {str(e)}')
                        )
                        continue

                self.stdout.write(self.style.SUCCESS(f'スクレイピング完了: {len(scraped_events)}件のイベントを取得'))
            else:
                self.stdout.write(
                    self.style.WARNING('該当するイベントは見つかりませんでした')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'スクレイピング実行エラー: {str(e)}')
            ) 