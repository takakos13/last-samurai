import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from ..models import ScrapedEvent
import logging

logger = logging.getLogger(__name__)

class LaBolaScraper:
    def __init__(self):
        self.base_url = "https://labola.jp/reserve/events/search/personal/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        print("LaBolaScraper initialized")

    def search_events(self, date=None, location=None, start_time=None, max_pages=10): #最大ページ
        print(f"\n検索開始: 日付={date}, 場所={location}, 開始時間={start_time}")
        events = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}?page={page}"
                print(f"\nページ {page} をスクレイピング中: {url}")
                
                response = requests.get(url, headers=self.headers)
                print(f"ステータスコード: {response.status_code}")
                
                if response.status_code != 200:
                    print("ページの取得に失敗しました")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                event_items = soup.find_all('li')
                print(f"検出されたイベント数: {len(event_items)}")
                
                for item in event_items:
                    try:
                        # 日付と場所の取得
                        date_location = item.find('div', class_='date')
                        if date_location:
                            date_location_text = date_location.text.strip()
                            print(f"日付場所テキスト: {date_location_text}")
                            
                            parts = date_location_text.split('｜')
                            if len(parts) >= 3:
                                event_date = parts[0].split('（')[0].strip()
                                event_location = parts[1].strip()
                                event_organizer = parts[2].strip()
                                
                                # 開始時間の取得
                                time_match = re.search(r'(\d{1,2}:\d{2})〜', date_location_text)
                                event_time = time_match.group(1) if time_match else None
                                
                                print(f"解析結果: 日付={event_date}, 場所={event_location}, 時間={event_time}")
                                
                                # イベント名の取得
                                event_name_tag = item.find('h2')
                                event_name = event_name_tag.text.strip() if event_name_tag else "不明"
                                
                                # URLの取得
                                event_url_tag = item.find('a', href=True)
                                full_event_url = f"https://labola.jp{event_url_tag['href']}" if event_url_tag else "不明"
                                
                                # クラスとカテゴリーの取得
                                class_info = item.find('div', class_='class-info')
                                event_class = class_info.text.strip() if class_info else "不明"
                                
                                category_info = item.find('div', class_='category')
                                event_category = category_info.text.strip() if category_info else "不明"
                                
                                # 募集人数の取得
                                capacity_info = item.find('th', string='募集数')
                                total = participants = spots_left = "不明"
                                
                                if capacity_info:
                                    capacity_td = capacity_info.find_next_sibling('td')
                                    if capacity_td:
                                        total_capacity = capacity_td.find('strong', class_='count')
                                        total = total_capacity.text.strip().split()[0] if total_capacity else "不明"
                                        
                                        participants_span = capacity_td.find('span', class_='green')
                                        if participants_span:
                                            participants_sum = participants_span.find('span', class_='sum')
                                            participants = participants_sum.text.strip() if participants_sum else "不明"
                                        
                                        remaining_span = capacity_td.find('span', class_='orange')
                                        if remaining_span:
                                            remaining_sum = remaining_span.find('span', class_='sum')
                                            spots_left = remaining_sum.text.strip() if remaining_sum else "不明"
                                
                                # 条件マッチング
                                if self._match_criteria(event_date, event_location, event_time, date, location, start_time):
                                    print(f"条件マッチ: {event_name}")
                                    events.append({
                                        'date': event_date,
                                        'location': event_location,
                                        'time': event_time,
                                        'organizer': event_organizer,
                                        'name': event_name,
                                        'url': full_event_url,
                                        'class': event_class,
                                        'category': event_category,
                                        'capacity': {
                                            'total': total,
                                            'participants': participants,
                                            'remaining': spots_left
                                        }
                                    })
                    
                    except Exception as e:
                        print(f"イベント解析エラー: {str(e)}")
                        continue
                
                time.sleep(1)
                
            except Exception as e:
                print(f"ページ {page} のスクレイピング中にエラー: {str(e)}")
                continue
        
        print(f"\n検索完了: {len(events)}件のイベントが見つかりました")
        return events

    def _match_criteria(self, event_date, event_location, event_time, target_date, target_location, target_time):
        print(f"\n条件マッチング:")
        print(f"イベント: 日付={event_date}, 場所={event_location}, 時間={event_time}")
        print(f"検索条件: 日付={target_date}, 場所={target_location}, 時間={target_time}")
        
        matches = True
        
        if target_date:
            try:
                # 検索条件の日付（YYYY-MM-DD）をYYYY/MM/DD形式に変換
                formatted_target_date = datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y/%m/%d')
                print(f"変換後の検索日付: {formatted_target_date}")
                date_match = formatted_target_date == event_date
                print(f"日付マッチ: {date_match}")
                matches &= date_match
            except ValueError as e:
                print(f"日付変換エラー: {e}")
                return False
        
        if target_location:
            location_match = target_location in event_location
            print(f"場所マッチ: {location_match}")
            matches &= location_match
        
        if target_time:
            time_match = target_time in event_time if event_time else False
            print(f"時間マッチ: {time_match}")
            matches &= time_match
        
        print(f"最終マッチング結果: {matches}")
        return matches

    def save_to_database(self, events):
        for event in events:
            try:
                # 日付文字列を datetime オブジェクトに変換
                date_obj = datetime.strptime(event['date'], '%Y/%m/%d').date()
                time_obj = datetime.strptime(event['time'], '%H:%M').time()

                ScrapedEvent.objects.create(
                    event_name=event['name'],
                    event_date=date_obj,
                    start_time=time_obj,
                    location=event['location'],
                    organizer=event['organizer'],
                    event_url=event['url'],
                    event_class=event['class'],
                    event_category=event['category'],
                    total_capacity=event['capacity']['total'],
                    participants=event['capacity']['participants'],
                    spots_left=event['capacity']['remaining']
                )
            except Exception as e:
                print(f"イベントの保存中にエラーが発生: {str(e)}")