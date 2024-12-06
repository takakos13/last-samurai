from django.db import models
from django.utils import timezone
from django.urls import reverse

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
    event_url = models.URLField(max_length=500)
    event_class = models.CharField(max_length=100)
    event_category = models.CharField(max_length=100)
    total_capacity = models.CharField(max_length=50)
    participants = models.CharField(max_length=50)
    spots_left = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date', 'start_time']

    def __str__(self):
        return f"{self.event_name} - {self.event_date}"

    def convert_to_facility_and_event(self):
        """スクレイピングしたイベントを施設とイベントモデルに変換して保存する"""
        # 施設を取得または作成
        facility, created = Facility.objects.get_or_create(
            court_name=self.organizer,
            location=self.location
        )

        # イベントの作成
        event = Event.objects.create(
            facility=facility,
            event_name=self.event_name,
            event_date=self.event_date,
            start_time=self.start_time,
            level_class=self.event_class,
            category=self.event_category,
            capacity=int(self.total_capacity) if self.total_capacity.isdigit() else 0,
            created_at=self.created_at
        )

        return facility, event
