from django.urls import path

from . import views

urlpatterns = [
    # Homepage e navigazione principale
    path('', views.HomeView.as_view(), name='home'),
    path('host/', views.HostHomeView.as_view(), name='host_home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('offline/', views.OfflineView.as_view(), name='offline'),
    
    # Gestione sessioni
    path('create/', views.CreateSessionView.as_view(), name='create_session'),
    path('host/<str:session_code>/', views.HostSessionView.as_view(), name='host_session'),
    
    # Unirsi e giocare
    path('join/', views.JoinSessionView.as_view(), name='join_session'),
    path('join/<str:session_code>/', views.JoinSessionView.as_view(), name='join_session_code'),
    path('session/<str:session_code>/', views.PlayerSessionView.as_view(), name='player_session'),
    
    # QR Code
    path('qr/<str:session_code>/', views.SessionQRView.as_view(), name='session_qr'),
    
    # API per AJAX
    path('api/sessions/<str:session_code>/stats/', views.SessionStatsView.as_view(), name='session_stats'),
    path('api/connection-info/', views.ConnectionInfoView.as_view(), name='connection_info'),
    path('api/sessions/<str:session_code>/players/<int:player_id>/cards/update/', 
         views.UpdatePlayerCardView.as_view(), name='update_player_card'),
    path('api/sessions/<str:session_code>/share-card/', 
         views.ShareCardView.as_view(), name='share_card'),
    path('api/sessions/<str:session_code>/end/', views.EndSessionView.as_view(), name='end_session'),
]