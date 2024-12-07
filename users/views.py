from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from .models import User, Reservation, Facility, Event, FavoriteFacility, ScrapedEvent
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from .utils.scraper import LaBolaScraper
import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)

def index(request):
    # ユーザー情報の取得
    users = User.objects.all().order_by('created_at')
    
    # 施設とイベントの取得
    facilities = Facility.objects.all().order_by('court_name')
    events = Event.objects.all().order_by('event_date', 'start_time')
    
    # ページネーションの設定（施設は20件、イベントは10件）
    facility_paginator = Paginator(facilities, 20)
    event_paginator = Paginator(events, 10)
    
    # GETパラメータからページ番号を取得
    facility_page = request.GET.get('facility_page')
    event_page = request.GET.get('event_page')
    
    try:
        facility_items = facility_paginator.page(facility_page)
    except PageNotAnInteger:
        facility_items = facility_paginator.page(1)
    except EmptyPage:
        facility_items = facility_paginator.page(facility_paginator.num_pages)
        
    try:
        event_items = event_paginator.page(event_page)
    except PageNotAnInteger:
        event_items = event_paginator.page(1)
    except EmptyPage:
        event_items = event_paginator.page(event_paginator.num_pages)
    
    context = {
        'users': users,
        'facilities': facility_items,
        'events': event_items,
    }
    return render(request, 'users/index.html', context)

class ReservationListView(ListView):
    model = Reservation
    template_name = 'users/reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(user_id=self.kwargs['user_id'])

class UserCreateView(CreateView):
    model = User
    template_name = 'users/user_form.html'
    fields = ['name', 'furigana', 'email', 'password', 'phone_number', 'gender', 'birth_date']
    success_url = reverse_lazy('users:index')

class ReservationCreateView(CreateView):
    model = Reservation
    template_name = 'users/reservation_form.html'
    fields = ['event']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        context['events'] = Event.objects.all().order_by('event_date', 'start_time')
        return context
    
    def form_valid(self, form):
        form.instance.user = get_object_or_404(User, pk=self.kwargs['user_id'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})

class ReservationUpdateView(UpdateView):
    model = Reservation
    template_name = 'users/reservation_form.html'
    fields = ['event']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        context['events'] = Event.objects.all().order_by('event_date', 'start_time')
        return context
    
    def form_valid(self, form):
        form.instance.user = get_object_or_404(User, pk=self.kwargs['user_id'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})

class UserRegisterView(CreateView):
    model = User
    template_name = 'users/register.html'
    fields = ['name', 'furigana', 'email', 'password', 'phone_number', 'gender', 'birth_date']
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.object.id})

def mypage(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    reservations = Reservation.objects.filter(user=user).order_by('event__event_date', 'event__start_time')
    favorite_facilities = FavoriteFacility.objects.filter(user=user).order_by('created_at')
    return render(request, 'users/mypage.html', {
        'user': user,
        'reservations': reservations,
        'favorite_facilities': favorite_facilities
    })

class UserUpdateView(UpdateView):
    model = User
    template_name = 'users/user_form.html'
    fields = ['name', 'furigana', 'email', 'phone_number', 'gender', 'birth_date']
    
    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})

class FacilityCreateView(CreateView):
    model = Facility
    template_name = 'users/facility_form.html'
    fields = ['court_name', 'location']
    success_url = reverse_lazy('users:index')

class FacilityDetailView(DetailView):
    model = Facility
    template_name = 'users/facility_detail.html'

class FacilityUpdateView(UpdateView):
    model = Facility
    template_name = 'users/facility_form.html'
    fields = ['court_name', 'location']

class EventCreateView(CreateView):
    model = Event
    template_name = 'users/event_form.html'
    fields = ['facility', 'event_name', 'event_date', 'start_time', 
             'level_class', 'category', 'capacity']
    success_url = reverse_lazy('users:index')

class EventUpdateView(UpdateView):
    model = Event
    template_name = 'users/event_form.html'
    fields = ['facility', 'event_name', 'event_date', 'start_time', 
             'level_class', 'category', 'capacity']
    success_url = reverse_lazy('users:index')

class EventDetailView(DetailView):
    model = Event
    template_name = 'users/event_detail.html'
    context_object_name = 'event'

class FavoriteFacilityCreateView(CreateView):
    model = FavoriteFacility
    template_name = 'users/favorite_facility_form.html'
    fields = ['facility']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        return context
    
    def form_valid(self, form):
        form.instance.user = get_object_or_404(User, pk=self.kwargs['user_id'])
        
        # 重複チェック
        existing = FavoriteFacility.objects.filter(
            user=form.instance.user,
            facility=form.cleaned_data['facility']
        )
        
        if existing.exists():
            form.add_error('facility', '既にお気に入りに登録されている施設です')
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})

class FavoriteFacilityUpdateView(UpdateView):
    model = FavoriteFacility
    template_name = 'users/favorite_facility_form.html'
    fields = ['facility']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        return context
    
    def form_valid(self, form):
        existing = FavoriteFacility.objects.filter(
            user_id=self.kwargs['user_id'],
            facility=form.cleaned_data['facility']
        ).exclude(pk=self.object.pk)
        
        if existing.exists():
            form.add_error('facility', '既にお気に入りに登録されている施設です')
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})

class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('users:index')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'メンバーを削除しました。')
        return super().delete(request, *args, **kwargs)

class FacilityDeleteView(DeleteView):
    model = Facility
    success_url = reverse_lazy('users:index')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '施設を削除しました。')
        return super().delete(request, *args, **kwargs)

class EventDeleteView(DeleteView):
    model = Event
    success_url = reverse_lazy('users:index')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'イベントを削除しました。')
        return super().delete(request, *args, **kwargs)

class FavoriteFacilityDeleteView(DeleteView):
    model = FavoriteFacility
    
    def get_success_url(self):
        return reverse_lazy('users:mypage', kwargs={'user_id': self.kwargs['user_id']})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'お気に入り施設を削除しました。')
        return super().delete(request, *args, **kwargs)

@ensure_csrf_cookie
def scrape_events(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        location = request.POST.get('location')
        start_time = request.POST.get('start_time')
        
        try:
            scraper = LaBolaScraper()
            events = scraper.search_events(date, location, start_time)
            
            for event in events:
                try:
                    # 日付と時間の変換
                    date_obj = datetime.strptime(event['date'], '%Y/%m/%d').date()
                    time_obj = datetime.strptime(event['time'], '%H:%M').time()

                    # ScrapedEventの作成
                    scraped_event = ScrapedEvent.objects.create(
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

                    # FacilityとEventの作成
                    facility, event_obj = scraped_event.convert_to_facility_and_event()
                    print(f"作成されたイベント: {event_obj}")

                except Exception as e:
                    print(f"イベントの保存中にエラー: {str(e)}")
                    continue

            # 検索結果をセッションに保存
            request.session['search_results'] = {
                'events': events,
                'search_params': {
                    'date': date,
                    'location': location,
                    'start_time': start_time
                }
            }
            
            return redirect('users:search_results')
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'エラーが発生しました: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': '不正なリクエストです'})

def search_results(request):
    # セッションから検索結果を取得
    search_results = request.session.get('search_results', {})
    events = search_results.get('events', [])
    search_params = search_results.get('search_params', {})
    
    return render(request, 'users/search_results.html', {
        'events': events,
        'search_params': search_params
    })
