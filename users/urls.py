from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.UserRegisterView.as_view(), name='user_register'),
    path('users/<int:user_id>/', views.mypage, name='mypage'),
    path('users/<int:user_id>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:user_id>/reservation/new/', views.ReservationCreateView.as_view(), name='reservation_new'),
    path('users/<int:user_id>/reservation/<int:pk>/edit/', views.ReservationUpdateView.as_view(), name='reservation_edit'),
    path('facility/<int:pk>/', views.FacilityDetailView.as_view(), name='facility_detail'),
    path('facility/<int:pk>/edit/', views.FacilityUpdateView.as_view(), name='facility_edit'),
    path('facility/new/', views.FacilityCreateView.as_view(), name='facility_new'),
    path('event/new/', views.EventCreateView.as_view(), name='event_new'),
    path('event/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:user_id>/favorite-facility/new/', views.FavoriteFacilityCreateView.as_view(), name='favorite_facility_new'),
    path('<int:user_id>/favorite-facility/<int:pk>/edit/', views.FavoriteFacilityUpdateView.as_view(), name='favorite_facility_edit'),
    path('<int:user_id>/favorite-facility/<int:pk>/delete/', views.FavoriteFacilityDeleteView.as_view(), name='favorite_facility_delete'),
    path('user/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('facility/<int:pk>/delete/', views.FacilityDeleteView.as_view(), name='facility_delete'),
    path('event/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('scrape/', views.scrape_events, name='scrape_events'),
    path('search-results/', views.search_results, name='search_results'),
]
