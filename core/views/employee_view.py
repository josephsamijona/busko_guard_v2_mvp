from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views import View
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Count, Q, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractDay
from datetime import timedelta
import calendar
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from collections import defaultdict
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
import json
from datetime import datetime, timedelta
import calendar
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import LeaveRequest

from ..models import AttendanceRecord, LeaveRequest
from ..utils import generate_qr_code

# Importation du modèle User personnalisé
User = get_user_model()

def login_view(request):
    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        # Rediriger directement vers la page d'accueil
        return redirect('home')
    
    # Initialiser la variable pour afficher/masquer l'alerte
    show_alert = False
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Afficher les données reçues en console pour debugging
        print(f"Tentative de connexion: username={username}, password={'*'*len(password if password else '')}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Si "Se souvenir de moi" n'est pas coché, la session expirera à la fermeture du navigateur
            if not remember_me:
                request.session.set_expiry(0)
            login(request, user)
            # Redirection après connexion réussie
            return redirect('home')  
        else:
            messages.error(request, "Identifiant ou mot de passe incorrect. Veuillez réessayer.")
            show_alert = True
    
    return render(request, 'login_employee.html', {'show_alert': show_alert})


@csrf_protect
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    # Votre code pour la vue home
    return render(request, 'employee_interface.html')



class EmployeeProfileDataView(LoginRequiredMixin, View):
    """Récupère les données de profil pour le dashboard"""
    def get(self, request):
        employee = request.user.employee_profile
        
        # Génération du QR code en base64 (suivant la même méthode que dans admin.py)
        qr_image_url = None
        if employee.qr_code:
            # Utiliser la même logique que dans admin.py
            import qrcode
            from io import BytesIO
            import base64
            
            # Création d'un QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(employee.qr_code)
            qr.make(fit=True)
            
            # Création d'une image à partir du QR code
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # URL de l'image au format base64
            qr_image_url = f"data:image/png;base64,{img_str}"
        
        data = {
            'employee_id': employee.employee_id,
            'name': f"{employee.user.first_name} {employee.user.last_name}",
            'department': employee.department.name if employee.department else None,
            'role': employee.role.name if employee.role else None,
            'qr_code_data': employee.qr_code,
            'qr_code_image': qr_image_url
        }
        return JsonResponse(data)
    
class AttendanceStatsView(LoginRequiredMixin, View):
    """Récupère les statistiques de présence et congés"""
    
    # Quota annuel de congés (à ajuster selon votre politique)
    ANNUAL_LEAVE_QUOTA = 25  
    
    def get(self, request):
        employee = request.user.employee_profile
        today = timezone.now().date()
        current_year = today.year
        
        # --- Statistiques du mois en cours ---
        month_start = today.replace(day=1)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        month_end = month_start.replace(day=days_in_month)
        
        # 1. Nombre de jours avec pointage dans le mois
        days_present = AttendanceRecord.objects.filter(
            employee=employee,
            record_type='IN',
            timestamp__date__gte=month_start,
            timestamp__date__lte=today
        ).dates('timestamp', 'day').count()
        
        # 2. Calcul du total d'heures travaillées ce mois-ci
        # Regroupe les entrées et sorties par jour pour calculer les heures
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date__gte=month_start,
            timestamp__date__lte=today,
            record_type__in=['IN', 'OUT']
        ).order_by('timestamp')
        
        total_hours = 0
        in_time = None
        
        for record in attendance_records:
            if record.record_type == 'IN':
                in_time = record.timestamp
            elif record.record_type == 'OUT' and in_time is not None:
                # Calcul de la différence en heures
                delta = record.timestamp - in_time
                total_hours += delta.total_seconds() / 3600
                in_time = None
        
        # 3. Jours d'absence (jours ouvrés - jours présent)
        # Note: Ceci est une approximation, il faudrait idéalement tenir compte
        # du calendrier des jours ouvrés spécifique à votre entreprise
        workdays_so_far = self._count_workdays(month_start, today)
        absences = workdays_so_far - days_present
        
        # --- Statistiques de congés pour l'année ---
        # 1. Calcul des jours de congés approuvés/utilisés
        leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            status='APPROVED',
            start_date__year=current_year
        )
        
        leave_days_used = 0
        for leave in leave_requests:
            # +1 car on compte le jour de début et le jour de fin
            delta = (leave.end_date - leave.start_date).days + 1
            leave_days_used += delta
        
        # 2. Calcul des jours de congés restants
        leave_days_remaining = self.ANNUAL_LEAVE_QUOTA - leave_days_used
        
        # 3. Congés en attente
        pending_leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            status='PENDING'
        ).count()
        
        # --- Formatage des résultats ---
        data = {
            'current_month': {
                'name': today.strftime('%B %Y'),
                'days_present': days_present,
                'days_absent': absences,
                'total_days': workdays_so_far,
                'presence_percentage': round((days_present / workdays_so_far * 100) if workdays_so_far > 0 else 0, 1),
                'total_hours_worked': round(total_hours, 1)
            },
            'leave': {
                'days_used': leave_days_used,
                'days_remaining': leave_days_remaining,
                'total_quota': self.ANNUAL_LEAVE_QUOTA,
                'pending_requests': pending_leave_requests
            }
        }
        
        return JsonResponse(data)
    
    def _count_workdays(self, start_date, end_date):
        """Compte le nombre de jours ouvrés entre deux dates (lundi-vendredi)"""
        days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 0-4 correspond à lundi-vendredi
                days += 1
            current_date += timedelta(days=1)
        return days
    
class AttendanceHistoryView(LoginRequiredMixin, View):
    """Récupère l'historique des pointages avec filtres et calcul des durées"""
    
    def get(self, request):
        employee = request.user.employee_profile
        
        # --- Paramètres de filtrage ---
        # 1. Période
        period = request.GET.get('period', 'week')  # Default: semaine en cours
        start_date = None
        end_date = None
        
        # Date personnalisée si fournie
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        
        if custom_start and custom_end:
            # Utilisation des dates personnalisées si fournies
            try:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            except ValueError:
                # Si format de date invalide, on ignore
                pass
        else:
            # Période prédéfinie
            today = timezone.now().date()
            if period == 'day':
                start_date = today
                end_date = today
            elif period == 'week':
                # Début de la semaine (lundi)
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'month':
                # Début du mois
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'year':
                # Début de l'année
                start_date = today.replace(month=1, day=1)
                end_date = today
        
        # 2. Type de pointage
        record_type = request.GET.get('record_type')
        
        # --- Construction de la requête ---
        query = AttendanceRecord.objects.filter(employee=employee)
        
        if start_date:
            query = query.filter(timestamp__date__gte=start_date)
        if end_date:
            query = query.filter(timestamp__date__lte=end_date)
        if record_type and record_type != 'ALL':
            query = query.filter(record_type=record_type)
            
        # Récupération des enregistrements, ordonnés par date/heure
        records = query.order_by('timestamp')
        
        # --- Organisation et traitement des données ---
        # Regrouper les pointages par jour pour faciliter l'affichage
        days_data = defaultdict(list)
        for record in records:
            day_str = record.timestamp.strftime('%Y-%m-%d')
            days_data[day_str].append({
                'id': record.id,
                'time': record.timestamp.strftime('%H:%M:%S'),
                'type': record.record_type,
                'type_display': record.get_record_type_display(),
                'location': record.location or '',
                'note': record.note or ''
            })
        
        # Calcul des durées de présence par jour
        days_summary = {}
        for day, day_records in days_data.items():
            # Initialisation des variables pour le calcul
            total_duration = 0
            in_time = None
            break_start = None
            
            # Parcourir les pointages du jour chronologiquement
            for record in sorted(day_records, key=lambda x: x['time']):
                if record['type'] == 'IN':
                    in_time = datetime.strptime(record['time'], '%H:%M:%S')
                elif record['type'] == 'OUT' and in_time is not None:
                    out_time = datetime.strptime(record['time'], '%H:%M:%S')
                    # Ajouter la durée entre entrée et sortie
                    delta = out_time - in_time
                    total_duration += delta.total_seconds()
                    in_time = None  # Réinitialiser pour le prochain cycle
                elif record['type'] == 'BREAK_START':
                    break_start = datetime.strptime(record['time'], '%H:%M:%S')
                elif record['type'] == 'BREAK_END' and break_start is not None:
                    break_end = datetime.strptime(record['time'], '%H:%M:%S')
                    # Soustraire la durée de la pause
                    delta = break_end - break_start
                    total_duration -= delta.total_seconds()
                    break_start = None  # Réinitialiser pour la prochaine pause
            
            # Convertir le total en heures et minutes
            hours = int(total_duration // 3600)
            minutes = int((total_duration % 3600) // 60)
            
            # Stocker le résumé du jour
            days_summary[day] = {
                'total_hours': hours,
                'total_minutes': minutes,
                'formatted_duration': f'{hours}h {minutes:02d}min',
                'records_count': len(day_records)
            }
        
        # --- Formatage du résultat ---
        result = []
        for day, records in sorted(days_data.items(), reverse=True):  # Tri des jours (plus récent d'abord)
            day_date = datetime.strptime(day, '%Y-%m-%d')
            day_info = {
                'date': day,
                'day_name': day_date.strftime('%A'),  # Nom du jour (lundi, mardi, etc.)
                'formatted_date': day_date.strftime('%d %B %Y'),  # Format lisible
                'records': sorted(records, key=lambda x: x['time']),  # Tri par heure
                'summary': days_summary.get(day, {'formatted_duration': '0h 00min'})
            }
            result.append(day_info)
        
        # --- Construction de la réponse ---
        response_data = {
            'success': True,
            'period': {
                'start': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end': end_date.strftime('%Y-%m-%d') if end_date else None,
            },
            'filter': record_type or 'ALL',
            'days': result,
            'total_records': sum(len(records) for records in days_data.values())
        }
        
        return JsonResponse(response_data)

class LeaveRequestListView(LoginRequiredMixin, View):
    """Vue pour lister les demandes de congé avec filtrage par statut"""
    
    def get(self, request):
        employee = request.user.employee_profile
        
        # Filtre par statut (PENDING, APPROVED, REJECTED, ou ALL)
        status_filter = request.GET.get('status', 'ALL')
        
        # Construction de la requête
        query = LeaveRequest.objects.filter(employee=employee)
        if status_filter != 'ALL':
            query = query.filter(status=status_filter)
            
        # Filtre par année
        year = request.GET.get('year')
        if year and year.isdigit():
            query = query.filter(start_date__year=int(year))
            
        # Tri par date de demande (plus récentes en premier)
        leaves = query.order_by('-request_date')
        
        # Formatage des résultats
        results = []
        for leave in leaves:
            # Calcul de la durée en jours
            duration = (leave.end_date - leave.start_date).days + 1
            
            # Formatage des dates pour l'affichage
            start_formatted = leave.start_date.strftime('%d %b %Y')
            end_formatted = leave.end_date.strftime('%d %b %Y')
            
            # Vérification si la demande peut être annulée
            can_cancel = leave.status == 'PENDING'
            
            # Nom du responsable ayant traité la demande (si applicable)
            processed_by = None
            if leave.response_by:
                processed_by = f"{leave.response_by.user.first_name} {leave.response_by.user.last_name}".strip()
                if not processed_by:
                    processed_by = leave.response_by.user.username
            
            results.append({
                'id': leave.id,
                'start_date': leave.start_date.strftime('%Y-%m-%d'),
                'end_date': leave.end_date.strftime('%Y-%m-%d'),
                'start_date_display': start_formatted,
                'end_date_display': end_formatted,
                'duration': duration,
                'type': leave.leave_type,
                'type_display': leave.get_leave_type_display(),
                'reason': leave.reason,
                'status': leave.status,
                'status_display': leave.get_status_display(),
                'request_date': leave.request_date.strftime('%Y-%m-%d %H:%M'),
                'response_date': leave.response_date.strftime('%Y-%m-%d %H:%M') if leave.response_date else None,
                'processed_by': processed_by,
                'can_cancel': can_cancel
            })
        
        # Statistiques des congés
        stats = self._get_leave_stats(employee)
        
        return JsonResponse({
            'success': True,
            'leaves': results,
            'count': len(results),
            'status_filter': status_filter,
            'stats': stats
        })
    
    def _get_leave_stats(self, employee):
        """Calcule les statistiques des demandes de congé"""
        current_year = timezone.now().year
        
        # Comptage par statut
        pending_count = LeaveRequest.objects.filter(
            employee=employee, 
            status='PENDING'
        ).count()
        
        approved_count = LeaveRequest.objects.filter(
            employee=employee, 
            status='APPROVED'
        ).count()
        
        rejected_count = LeaveRequest.objects.filter(
            employee=employee, 
            status='REJECTED'
        ).count()
        
        # Jours approuvés cette année
        approved_requests = LeaveRequest.objects.filter(
            employee=employee,
            status='APPROVED',
            start_date__year=current_year
        )
        
        days_used = 0
        for leave in approved_requests:
            days_used += (leave.end_date - leave.start_date).days + 1
        
        return {
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'total_count': pending_count + approved_count + rejected_count,
            'days_used_this_year': days_used
        }

class LeaveRequestCreateView(LoginRequiredMixin, View):
    """Vue pour créer une nouvelle demande de congé"""
    
    def post(self, request):
        employee = request.user.employee_profile
        
        try:
            # Récupération des données du formulaire
            data = json.loads(request.body)
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            leave_type = data.get('leave_type')
            reason = data.get('reason', '')
            
            # Validation des champs obligatoires
            if not all([start_date_str, end_date_str, leave_type]):
                return JsonResponse({
                    'success': False, 
                    'error': 'Tous les champs requis doivent être remplis.'
                }, status=400)
            
            # Conversion des dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Format de date invalide. Utilisez le format YYYY-MM-DD.'
                }, status=400)
            
            # Validation des dates
            today = timezone.now().date()
            if start_date < today:
                return JsonResponse({
                    'success': False, 
                    'error': 'La date de début ne peut pas être dans le passé.'
                }, status=400)
            
            if end_date < start_date:
                return JsonResponse({
                    'success': False, 
                    'error': 'La date de fin ne peut pas être antérieure à la date de début.'
                }, status=400)
            
            # Vérification des chevauchements avec d'autres demandes
            overlapping = LeaveRequest.objects.filter(
                employee=employee,
                status='APPROVED',
            ).filter(
                # Chevauchement: la nouvelle demande commence pendant une existante
                # ou se termine pendant une existante
                Q(start_date__lte=end_date, end_date__gte=start_date)
            ).exists()
            
            if overlapping:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cette période chevauche une demande de congé déjà approuvée.'
                }, status=400)
            
            # Création de la demande de congé
            with transaction.atomic():
                leave_request = LeaveRequest.objects.create(
                    employee=employee,
                    start_date=start_date,
                    end_date=end_date,
                    leave_type=leave_type,
                    reason=reason,
                    status='PENDING',
                    request_date=timezone.now()
                )
            
            # Calcul de la durée
            duration = (end_date - start_date).days + 1
            
            return JsonResponse({
                'success': True,
                'id': leave_request.id,
                'message': 'Demande de congé créée avec succès.',
                'duration': duration,
                'start_date': start_date_str,
                'end_date': end_date_str
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Une erreur est survenue: {str(e)}'
            }, status=500)

class LeaveRequestActionView(LoginRequiredMixin, View):
    """Vue pour gérer les actions sur les demandes de congé (annulation)"""
    
    def post(self, request, leave_id):
        employee = request.user.employee_profile
        action = request.GET.get('action', 'cancel')
        
        try:
            # Récupération de la demande de congé
            leave_request = get_object_or_404(
                LeaveRequest,
                id=leave_id,
                employee=employee
            )
            
            # Vérification si l'action est possible
            if action == 'cancel':
                if leave_request.status != 'PENDING':
                    return JsonResponse({
                        'success': False,
                        'error': 'Seules les demandes en attente peuvent être annulées.'
                    }, status=400)
                
                # Annulation de la demande
                leave_request.status = 'REJECTED'  # Ou utiliser un statut spécifique 'CANCELLED'
                leave_request.response_date = timezone.now()
                leave_request.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Demande de congé annulée avec succès.',
                    'id': leave_id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Action non reconnue.'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Une erreur est survenue: {str(e)}'
            }, status=500)

class LeaveRequestDetailView(LoginRequiredMixin, View):
    """Vue pour afficher les détails d'une demande de congé spécifique"""
    
    def get(self, request, leave_id):
        employee = request.user.employee_profile
        
        try:
            # Récupération de la demande de congé
            leave = get_object_or_404(
                LeaveRequest,
                id=leave_id,
                employee=employee
            )
            
            # Calcul de la durée
            duration = (leave.end_date - leave.start_date).days + 1
            
            # Nom du responsable ayant traité la demande (si applicable)
            processed_by = None
            if leave.response_by:
                processed_by = f"{leave.response_by.user.first_name} {leave.response_by.user.last_name}".strip()
                if not processed_by:
                    processed_by = leave.response_by.user.username
            
            # Construction du résultat
            result = {
                'id': leave.id,
                'start_date': leave.start_date.strftime('%Y-%m-%d'),
                'end_date': leave.end_date.strftime('%Y-%m-%d'),
                'start_date_display': leave.start_date.strftime('%d %b %Y'),
                'end_date_display': leave.end_date.strftime('%d %b %Y'),
                'duration': duration,
                'type': leave.leave_type,
                'type_display': leave.get_leave_type_display(),
                'reason': leave.reason,
                'status': leave.status,
                'status_display': leave.get_status_display(),
                'request_date': leave.request_date.strftime('%Y-%m-%d %H:%M'),
                'response_date': leave.response_date.strftime('%Y-%m-%d %H:%M') if leave.response_date else None,
                'processed_by': processed_by,
                'can_cancel': leave.status == 'PENDING'
            }
            
            return JsonResponse({
                'success': True,
                'leave': result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Une erreur est survenue: {str(e)}'
            }, status=500)