from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import pre_delete
from django.dispatch import receiver

#ユーザーモデル　　＊Djangoのユーザーモデルをベースに
class User(models.Model):
    name = models.CharField(max_length=200)
    furigana = models.CharField(max_length=200)
    email = models.EmailField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=200, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('users:index')

#施設モデル　
class Facility(models.Model):
    court_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.court_name} - {self.location}"

    def get_absolute_url(self):
        return reverse('users:facility_detail', kwargs={'pk': self.pk})

#イベントモデル
class Event(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='events')
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    start_time = models.TimeField()
    level_class = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    capacity = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event_name', 'event_date', 'start_time', 'facility']
        ordering = ['event_date', 'start_time']

    def delete(self, *args, **kwargs):
        # 関連するScrapedEventを検索して削除
        try:
            scraped_events = ScrapedEvent.objects.filter(
                event_name=self.event_name,
                event_date=self.event_date,
                start_time=self.start_time,
                location=self.facility.location,
                organizer=self.facility.court_name
            )
            for scraped_event in scraped_events:
                scraped_event.event = None  # 関連を解除
                scraped_event.save()
                scraped_event.delete()
        except Exception as e:
            print(f"Error deleting ScrapedEvent: {e}")

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.event_name} - {self.facility.court_name}"

    def get_absolute_url(self):
        return reverse('users:event_detail', kwargs={'pk': self.pk})

#予約モデル　
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        event_info = f" - {self.event.event_name}" if self.event else ""
        return f"{self.user.name}の予約{event_info}"

    class Meta:
        ordering = ['-created_at']

#お気に入り施設モデル
class FavoriteFacility(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.name} - {self.facility.court_name}"

    class Meta:
        unique_together = ['user', 'facility']


class ScrapedEvent(models.Model):
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    start_time = models.TimeField()
    location = models.CharField(max_length=200)
    organizer = models.CharField(max_length=200)
    event_url = models.URLField(max_length=500, unique=True)
    event_class = models.CharField(max_length=100)
    event_category = models.CharField(max_length=100)
    total_capacity = models.CharField(max_length=50)
    participants = models.CharField(max_length=50)
    spots_left = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.OneToOneField('Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='scraped_source')

    class Meta:
        ordering = ['event_date', 'start_time']
        unique_together = ['event_name', 'event_date', 'start_time', 'location']

    def delete(self, *args, **kwargs):
        print(f"Starting deletion of ScrapedEvent: {self.event_name} on {self.event_date}")
        
        try:
            # まず施設を検索
            facility = Facility.objects.get(
                court_name=self.organizer,
                location=self.location
            )
            print(f"Found facility: {facility.court_name}")

            # 施設に紐づくイベントを検索
            event = Event.objects.get(
                facility=facility,
                event_name=self.event_name,
                event_date=self.event_date,
                start_time=self.start_time
            )
            print(f"Found matching event: {event.event_name}")

            # イベントを削除
            event_id = event.id
            event.delete()
            print(f"Deleted event with ID: {event_id}")

        except Facility.DoesNotExist:
            print(f"No facility found for: {self.organizer} at {self.location}")
        except Event.DoesNotExist:
            print(f"No matching event found")
        except Exception as e:
            print(f"Unexpected error during event deletion: {e}")
        
        print("Proceeding with ScrapedEvent deletion")
        result = super().delete(*args, **kwargs)
        print("ScrapedEvent deletion completed")
        return result

    def convert_to_facility_and_event(self):
        """スクレイピングしたイベントを施設とイベントモデルに変換して保存する"""
        try:
            # 施設を取得または作成
            facility, _ = Facility.objects.get_or_create(
                court_name=self.organizer,
                location=self.location
            )

            # 既存のイベントを探す
            try:
                event = Event.objects.get(
                    event_name=self.event_name,
                    event_date=self.event_date,
                    start_time=self.start_time,
                    facility=facility
                )
                # 既存のイベントを更新
                event.level_class = self.event_class
                event.category = self.event_category
                event.capacity = int(self.total_capacity) if self.total_capacity.isdigit() else 0
                event.save()
            except Event.DoesNotExist:
                # 新規イベントを作成
                event = Event.objects.create(
                    facility=facility,
                    event_name=self.event_name,
                    event_date=self.event_date,
                    start_time=self.start_time,
                    level_class=self.event_class,
                    category=self.event_category,
                    capacity=int(self.total_capacity) if self.total_capacity.isdigit() else 0
                )

            # ScrapedEventとEventを関連付け
            self.event = event
            self.save()

            return facility, event

        except Exception as e:
            print(f"Error in convert_to_facility_and_event: {e}")
            raise

# シグナルハン�ラーの定義
@receiver(pre_delete, sender=ScrapedEvent)
def delete_related_event(sender, instance, **kwargs):
    """ScrapedEventが削除される前に関連するEventを削除"""
    try:
        # 関連するEventを検索
        facility = Facility.objects.get(
            court_name=instance.organizer,
            location=instance.location
        )
        events = Event.objects.filter(
            facility=facility,
            event_name=instance.event_name,
            event_date=instance.event_date,
            start_time=instance.start_time
        )
        # 見つかったEventを削除
        events.delete()
    except Exception as e:
        print(f"Error in delete_related_event signal: {e}")

@receiver(pre_delete, sender=Event)
def delete_related_scraped_event(sender, instance, **kwargs):
    """Eventが削除される前に関連するScrapedEventを削除"""
    try:
        # 関連するScrapedEventを検索
        scraped_events = ScrapedEvent.objects.filter(
            event_name=instance.event_name,
            event_date=instance.event_date,
            start_time=instance.start_time,
            location=instance.facility.location,
            organizer=instance.facility.court_name
        )
        # 見つかったScrapedEventを削除
        scraped_events.delete()
    except Exception as e:
        print(f"Error in delete_related_scraped_event signal: {e}")
