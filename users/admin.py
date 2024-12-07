from django.contrib import admin
from .models import User, Reservation, Facility, Event, FavoriteFacility, ScrapedEvent

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'furigana', 'email', 'phone_number', 'gender', 'birth_date', 'created_at', 'updated_at')
    search_fields = ('name', 'furigana', 'email', 'phone_number', 'gender', 'birth_date')
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "選択したユーザーを削除"

class ReservationAdmin(admin.ModelAdmin):
    def get_event_date(self, obj):
        return obj.event.event_date if obj.event else None
    get_event_date.short_description = '予約日'

    def get_court_name(self, obj):
        return obj.event.facility.court_name if obj.event else None
    get_court_name.short_description = '主催者'

    def get_event_name(self, obj):
        return obj.event.event_name if obj.event else None
    get_event_name.short_description = 'イベント名'

    list_display = ('user', 'id', 'get_court_name', 'get_event_name', 'get_event_date', 'created_at')
    list_filter = ('event__facility__court_name', 'event__event_date')
    date_hierarchy = 'event__event_date'
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "選択した予約を削除"

class FacilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_name', 'location')
    search_fields = ('court_name', 'location')

class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_name', 'facility', 'event_date', 'start_time', 
                   'level_class', 'category', 'capacity', 'created_at')
    list_filter = ('facility', 'event_date', 'level_class', 'category')
    search_fields = ('event_name', 'facility__court_name')
    date_hierarchy = 'event_date'
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "選択したイベントを削除"

class FavoriteFacilityAdmin(admin.ModelAdmin):
    # コート名を取得するメソッド
    def get_court_name(self, obj):
        return obj.facility.court_name
    get_court_name.short_description = '主催者'

    # 場所を取得するメソッド
    def get_location(self, obj):
        return obj.facility.location
    get_location.short_description = '場所'

    list_display = ('user', 'get_court_name', 'get_location', 'created_at')
    list_filter = ('facility__court_name', 'user__name')
    search_fields = ('user__name', 'facility__court_name')
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "選択したお気に入りを削除"

@admin.register(ScrapedEvent)
class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = (
        'event_name',
        'event_date',
        'start_time',
        'location',
        'organizer',
        'event_class',
        'event_category',
        'total_capacity',
        'participants',
        'spots_left',
        'created_at'
    )
    list_filter = ('event_date', 'organizer', 'event_class', 'event_category')
    search_fields = ('event_name', 'location', 'organizer')
    date_hierarchy = 'event_date'
    ordering = ('event_date', 'start_time')
    readonly_fields = ('created_at',)

admin.site.register(User, UserAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Facility, FacilityAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(FavoriteFacility, FavoriteFacilityAdmin)
# Register your models here.
