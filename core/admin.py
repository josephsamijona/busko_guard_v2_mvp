# Fichier : admin.py
#
# Description : Configuration de l'interface d'administration Django pour l'application de gestion RH.
#               Ce fichier définit comment les modèles sont présentés dans l'interface d'administration,
#               ainsi que des fonctionnalités supplémentaires (actions, filtres, etc.).

from django.contrib import admin

# Personnalisation de l'interface d'administration
admin.site.site_header = "buskoguard Système de Gestion de Présence"
admin.site.site_title = "Administration"
admin.site.index_title = "Tableau de Bord"
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
import base64

# Importation des modèles
from .models import Department, Role, User, Employee, Schedule, AttendanceRecord, LeaveRequest

# --- Section 1: Inlines pour afficher des données liées ---

class EmployeeInline(admin.StackedInline):
    """Affiche les informations de l'employé directement dans la page de l'utilisateur."""
    model = Employee
    can_delete = False
    verbose_name_plural = 'Profil employé'

class ScheduleInline(admin.TabularInline):
    """Affiche les horaires d'un employé directement dans sa page."""
    model = Schedule
    extra = 1
    verbose_name_plural = 'Horaires de travail'

class AttendanceRecordInline(admin.TabularInline):
    """Affiche les pointages récents d'un employé directement dans sa page."""
    model = AttendanceRecord
    extra = 0
    verbose_name_plural = 'Pointages récents'
    max_num = 10  # Limite le nombre de pointages affichés
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        """Limite les pointages aux 10 derniers jours."""
        queryset = super().get_queryset(request)
        return queryset.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=10))

class LeaveRequestInline(admin.TabularInline):
    """Affiche les demandes de congé d'un employé directement dans sa page."""
    model = LeaveRequest
    fk_name = 'employee'  # Spécifie quelle relation ForeignKey utiliser
    extra = 0
    verbose_name_plural = 'Demandes de congé'
    max_num = 5  # Limite le nombre de demandes affichées
    ordering = ['-request_date']
    fields = ('start_date', 'end_date', 'leave_type', 'status', 'reason')
    readonly_fields = ('status',)

# --- Section 2: Configuration des modèles d'organisation ---

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les départements."""
    list_display = ('name', 'description', 'employee_count')
    search_fields = ('name', 'description')
    
    def employee_count(self, obj):
        """Affiche le nombre d'employés dans ce département."""
        count = Employee.objects.filter(department=obj).count()
        return count
    employee_count.short_description = 'Nombre d\'employés'
    
    def get_queryset(self, request):
        """Ajoute un comptage des employés à la requête."""
        queryset = super().get_queryset(request)
        return queryset.annotate(employee_count=Count('employee'))

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les rôles."""
    list_display = ('name', 'description', 'employee_count')
    search_fields = ('name', 'description')
    
    def employee_count(self, obj):
        """Affiche le nombre d'employés ayant ce rôle."""
        count = Employee.objects.filter(role=obj).count()
        return count
    employee_count.short_description = 'Nombre d\'employés'
    
    def get_queryset(self, request):
        """Ajoute un comptage des employés à la requête."""
        queryset = super().get_queryset(request)
        return queryset.annotate(employee_count=Count('employee'))

# --- Section 3: Configuration du modèle Utilisateur ---

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configuration de l'interface d'administration pour les utilisateurs."""
    fieldsets = UserAdmin.fieldsets + (
        ('Informations personnelles supplémentaires', {
            'fields': ('date_of_birth', 'phone_number', 'address', 'profile_picture')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'has_employee_profile')
    list_filter = UserAdmin.list_filter + ('date_of_birth',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    inlines = [EmployeeInline]
    
    def has_employee_profile(self, obj):
        """Vérifie si l'utilisateur a un profil employé associé."""
        try:
            return bool(obj.employee_profile)
        except Employee.DoesNotExist:
            return False
    has_employee_profile.boolean = True
    has_employee_profile.short_description = 'Profil employé'

# --- Section 4: Configuration du modèle Employé ---

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les employés."""
    list_display = ('employee_id', 'get_full_name', 'department', 'role', 'get_email', 'get_phone', 'has_nfc', 'has_qrcode')
    list_filter = ('department', 'role', 'user__is_active')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'nfc_id')
    readonly_fields = ('nfc_id', 'qr_code', 'qr_code_display')
    inlines = [ScheduleInline, LeaveRequestInline, AttendanceRecordInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'employee_id', 'department', 'role')
        }),
        ('Identification (générée automatiquement)', {
            'fields': ('nfc_id', 'qr_code', 'qr_code_display')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Génère automatiquement un ID NFC et un QR code lors de la création d'un employé.
        """
        # Si c'est une nouvelle création (pas une modification)
        if not change:
            # Génération d'un identifiant NFC unique
            obj.nfc_id = f"NFC-{uuid.uuid4().hex[:12].upper()}"
            
            # Génération d'un QR code unique
            obj.qr_code = f"EMP-{obj.employee_id}-{uuid.uuid4().hex[:8].upper()}"
            
        # Sauvegarde le modèle
        super().save_model(request, obj, form, change)
    
    def get_full_name(self, obj):
        """Récupère le nom complet de l'utilisateur."""
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Nom complet'
    get_full_name.admin_order_field = 'user__last_name'
    
    def get_email(self, obj):
        """Récupère l'email de l'utilisateur."""
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_phone(self, obj):
        """Récupère le numéro de téléphone de l'utilisateur."""
        return obj.user.phone_number
    get_phone.short_description = 'Téléphone'
    
    def has_nfc(self, obj):
        """Vérifie si l'employé a un identifiant NFC."""
        return bool(obj.nfc_id)
    has_nfc.boolean = True
    has_nfc.short_description = 'NFC'
    
    def has_qrcode(self, obj):
        """Vérifie si l'employé a un QR code."""
        return bool(obj.qr_code)
    has_qrcode.boolean = True
    has_qrcode.short_description = 'QR Code'
    
    def qr_code_display(self, obj):
        """Affiche le QR code de l'employé s'il existe."""
        if obj.qr_code:
            # Création d'un QR code pour l'affichage
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(obj.qr_code)
            qr.make(fit=True)
            
            # Création d'une image à partir du QR code
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Renvoie une image HTML
            return format_html('<img src="data:image/png;base64,{}" width="150" height="150"/>', img_str)
        return "Aucun QR code généré"
    qr_code_display.short_description = 'Aperçu du QR Code'
    
    # Note: Les actions de génération manuelle sont supprimées car la génération est maintenant automatique

# --- Section 5: Configuration du modèle Schedule (Horaires) ---

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les horaires."""
    list_display = ('employee', 'get_day_display', 'start_time', 'end_time', 'break_duration')
    list_filter = ('day_of_week', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name')
    
    def get_day_display(self, obj):
        """Récupère le jour de la semaine formaté."""
        return obj.get_day_of_week_display()
    get_day_display.short_description = 'Jour'
    get_day_display.admin_order_field = 'day_of_week'
    
    def break_duration(self, obj):
        """Calcule la durée de la pause si définie."""
        if obj.break_start and obj.break_end:
            # Conversion en minutes pour faciliter le calcul
            break_start_minutes = obj.break_start.hour * 60 + obj.break_start.minute
            break_end_minutes = obj.break_end.hour * 60 + obj.break_end.minute
            duration_minutes = break_end_minutes - break_start_minutes
            
            # Formatage heures/minutes
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            
            if hours > 0:
                return f"{hours}h{minutes:02d}"
            else:
                return f"{minutes} min"
        return "-"
    break_duration.short_description = 'Durée de pause'

# --- Section 6: Configuration du modèle AttendanceRecord (Pointages) ---

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les pointages."""
    list_display = ('employee', 'timestamp', 'record_type', 'location')
    list_filter = ('record_type', 'timestamp', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name', 'location', 'note')
    date_hierarchy = 'timestamp'
    
    actions = ['export_attendance_records']
    
    def export_attendance_records(self, request, queryset):
        """Action pour "exporter" les pointages sélectionnés (simulation)."""
        # Cette action est une simulation - dans un cas réel, on générerait un fichier CSV/Excel
        count = queryset.count()
        self.message_user(request, f"{count} enregistrement(s) marqué(s) pour export. L'export sera disponible prochainement.")
    export_attendance_records.short_description = "Exporter les pointages sélectionnés"

# --- Section 7: Configuration du modèle LeaveRequest (Demandes de congé) ---

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les demandes de congé."""
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'duration_days', 'status', 'request_date')
    list_filter = ('status', 'leave_type', 'start_date', 'request_date', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name', 'reason')
    date_hierarchy = 'request_date'
    readonly_fields = ('request_date',)
    
    fieldsets = (
        ('Informations de la demande', {
            'fields': ('employee', 'start_date', 'end_date', 'leave_type', 'reason')
        }),
        ('Statut', {
            'fields': ('status', 'request_date', 'response_date', 'response_by')
        }),
    )
    
    actions = ['approve_leave_requests', 'reject_leave_requests']
    
    def duration_days(self, obj):
        """Calcule la durée en jours de la demande de congé."""
        delta = obj.end_date - obj.start_date
        # +1 car on compte le jour de début et le jour de fin
        return delta.days + 1
    duration_days.short_description = 'Durée (jours)'
    
    def approve_leave_requests(self, request, queryset):
        """Action pour approuver les demandes de congé sélectionnées."""
        # Récupération de l'utilisateur admin actuel pour le champ response_by
        admin_employee = None
        if hasattr(request.user, 'employee_profile'):
            admin_employee = request.user.employee_profile
        
        # Mise à jour des demandes sélectionnées
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            response_date=timezone.now(),
            response_by=admin_employee
        )
        
        self.message_user(request, f"{updated} demande(s) de congé approuvée(s) avec succès.")
    approve_leave_requests.short_description = "Approuver les demandes sélectionnées"
    
    def reject_leave_requests(self, request, queryset):
        """Action pour rejeter les demandes de congé sélectionnées."""
        # Récupération de l'utilisateur admin actuel pour le champ response_by
        admin_employee = None
        if hasattr(request.user, 'employee_profile'):
            admin_employee = request.user.employee_profile
        
        # Mise à jour des demandes sélectionnées
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            response_date=timezone.now(),
            response_by=admin_employee
        )
        
        self.message_user(request, f"{updated} demande(s) de congé rejetée(s).")
    reject_leave_requests.short_description = "Rejeter les demandes sélectionnées"