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
    event_name = models.CharField(max_length=200, blank=True, null=True)
    event_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    level_class = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event_name', 'event_date', 'start_time', 'facility']
        ordering = ['event_date', 'start_time']

    def delete(self, *args, **kwargs):
        if hasattr(self, '_deleting_related'):
            return super().delete(*args, **kwargs)
        
        try:
            self._deleting_related = True
            if hasattr(self, 'scraped_source') and self.scraped_source:
                self.scraped_source.delete()
        except Exception:
            pass
        finally:
            delattr(self, '_deleting_related')
        
        return super().delete(*args, **kwargs)

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
        try:
            # まず施設を検索
            facility = Facility.objects.get(
                court_name=self.organizer,
                location=self.location
            )

            # 施設に紐づくイベントを検索
            event = Event.objects.get(
                facility=facility,
                event_name=self.event_name,
                event_date=self.event_date,
                start_time=self.start_time
            )

            # イベントを削除
            event.delete()

        except Facility.DoesNotExist:
            pass
        except Event.DoesNotExist:
            pass
        except Exception as e:
            pass
        
        return super().delete(*args, **kwargs)

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

# シグナルハンドラーの定義
@receiver(pre_delete, sender=ScrapedEvent)
def delete_related_event(sender, instance, **kwargs):
    """ScrapedEventが削除される前に関連するEventを削除"""
    if hasattr(instance, '_deleting_related'):
        return
    
    try:
        instance._deleting_related = True
        # 施設を検索
        facility = Facility.objects.filter(
            court_name=instance.organizer,
            location=instance.location
        ).first()
        
        if facility:
            # イベントを検索して削除
            Event.objects.filter(
                facility=facility,
                event_name=instance.event_name,
                event_date=instance.event_date,
                start_time=instance.start_time
            ).delete()
    except Exception:
        pass
    finally:
        delattr(instance, '_deleting_related')

@receiver(pre_delete, sender=Event)
def delete_related_scraped_event(sender, instance, **kwargs):
    """Eventが削除される前に関連するScrapedEventを削除"""
    if hasattr(instance, '_deleting_related'):
        return
    
    try:
        instance._deleting_related = True
        # ScrapedEventを検索して削除
        ScrapedEvent.objects.filter(
            event_name=instance.event_name,
            event_date=instance.event_date,
            start_time=instance.start_time,
            location=instance.facility.location,
            organizer=instance.facility.court_name
        ).delete()
    except Exception:
        pass
    finally:
        delattr(instance, '_deleting_related')
