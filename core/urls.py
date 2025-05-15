# core/urls.py
from django.urls import path
from core.views.employee_view import login_view,logout_view,home_view,EmployeeProfileDataView,AttendanceStatsView,AttendanceHistoryView,LeaveRequest,LeaveRequestActionView,LeaveRequestCreateView,LeaveRequestDetailView,LeaveRequestListView
from core.views.kiosk_view import kiosk_view,get_csrf_token,authenticate_card,record_attendance
urlpatterns = [
    # Autres URLs existantes...
    
    # API pour le kiosque
    path('', kiosk_view, name='kiosk'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('api/profile/', 
        EmployeeProfileDataView.as_view(), 
        name='api_profile'),
    
    # === Statistiques ===
    path('api/stats/', 
        AttendanceStatsView.as_view(), 
         name='api_stats'),
    
    # === Historique des pointages ===
    path('api/attendance/history/', 
        AttendanceHistoryView.as_view(), 
         name='api_attendance_history'),
    
    # === Demandes de congés ===
    # Liste des demandes de congé avec filtres
    path('api/leaves/', 
        LeaveRequestListView.as_view(), 
         name='api_leaves_list'),
    
    # Création d'une nouvelle demande
    path('api/leaves/create/', 
        LeaveRequestCreateView.as_view(), 
         name='api_leaves_create'),
    
    # Détails d'une demande spécifique
    path('api/leaves/<int:leave_id>/', 
        LeaveRequestDetailView.as_view(), 
         name='api_leaves_detail'),
    
    # Actions sur une demande (annulation)
    path('api/leaves/<int:leave_id>/action/', 
        LeaveRequestActionView.as_view(), 
         name='api_leaves_action'),
    # URL pour obtenir le token CSRF (utilisé par le client JavaScript du kiosque)
    path('api/get-csrf-token/', get_csrf_token, name='get_csrf_token'),

    # URL pour l'API d'authentification par carte (NFC ou QR code)
    # Cette URL sera appelée par le JavaScript du kiosque lors de la lecture d'une carte/QR
    path('api/authenticate-card/', authenticate_card, name='authenticate_card'),

    # URL pour l'API d'enregistrement d'un pointage
    # Cette URL sera appelée par le JavaScript du kiosque après authentification pour enregistrer une action
    path('api/record-attendance/', record_attendance, name='record_attendance'),

]