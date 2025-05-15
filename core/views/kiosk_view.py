from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from ..models import Employee,AttendanceRecord
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect











@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Vue simple pour s'assurer que le client a un token CSRF.
    Cette vue sera appelée au chargement de la page kiosque.
    """
    return JsonResponse({"success": True})

def kiosk_view(request):
    """
    Vue principale du kiosque de pointage des présences.
    Affiche l'interface avec les options QR et NFC.
    """
    # Configuration JavaScript pour le kiosque

    
    return render(request, 'kiosk.html')

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.utils import timezone
import json

from ..models import Employee, User, AttendanceRecord

@csrf_exempt
@require_POST
def authenticate_card(request):
    """
    Vue pour authentifier un employé via son identifiant NFC ou QR code.
    Reçoit les données au format JSON et retourne le statut de l'authentification
    ainsi que les actions de pointage disponibles.
    """
    try:
        # Charger les données de la requête
        data = json.loads(request.body)
        
        # Vérifier si on a un identifiant NFC ou QR code
        nfc_id = data.get('nfc_id')
        qr_code = data.get('qr_code')
        
        if not nfc_id and not qr_code:
            return JsonResponse({
                "success": False,
                "error": "Aucun identifiant NFC ou QR code fourni"
            }, status=400)
            
        # Rechercher l'employé correspondant
        employee = None
        
        if nfc_id:
            try:
                employee = Employee.objects.get(nfc_id=nfc_id)
            except Employee.DoesNotExist:
                pass
                
        if qr_code and not employee:
            try:
                employee = Employee.objects.get(qr_code=qr_code)
            except Employee.DoesNotExist:
                pass
                
        if not employee:
            return JsonResponse({
                "success": False,
                "error": "Aucun employé trouvé avec cet identifiant"
            }, status=404)
            
        # Authentifier l'utilisateur
        user = employee.user
        
        # Connexion de l'utilisateur à la session (optionnel)
        if request.session.session_key is None:
            request.session.create()
        login(request, user)
        
        # Déterminer les actions de pointage disponibles en fonction du dernier pointage
        available_actions = get_available_actions(employee)
        
        # Retourner les informations de base de l'employé et les actions disponibles
        return JsonResponse({
            "success": True,
            "employee_id": employee.employee_id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "user_id": user.id,
            "department": employee.department.name if employee.department else None,
            "role": employee.role.name if employee.role else None,
            "available_actions": available_actions
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Format JSON invalide"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }, status=500)

@csrf_exempt
@require_POST
def record_attendance(request):
    """
    Vue pour enregistrer un pointage après authentification.
    
    Le corps de la requête doit contenir:
    - employee_id: L'identifiant de l'employé
    - record_type: Le type de pointage ('IN', 'OUT', 'BREAK_START', 'BREAK_END')
    - location: (optionnel) Le lieu du pointage
    - note: (optionnel) Une note associée au pointage
    
    Retourne:
    - En cas de succès: {"success": true, "timestamp": "...", "record_id": ...}
    - En cas d'échec: {"success": false, "error": "Message d'erreur"}
    """
    try:
        # Vérifier que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return JsonResponse({
                "success": False,
                "error": "Utilisateur non authentifié"
            }, status=401)
            
        # Charger les données de la requête
        data = json.loads(request.body)
        
        # Récupérer l'employé à partir de son ID
        employee_id = data.get('employee_id')
        if not employee_id:
            return JsonResponse({
                "success": False,
                "error": "ID employé non fourni"
            }, status=400)
            
        try:
            employee = Employee.objects.get(employee_id=employee_id)
            
            # Vérifier que l'utilisateur connecté est bien l'employé concerné
            if request.user.id != employee.user.id:
                return JsonResponse({
                    "success": False,
                    "error": "Non autorisé à enregistrer un pointage pour cet employé"
                }, status=403)
                
        except Employee.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Employé non trouvé"
            }, status=404)
            
        # Récupérer le type de pointage
        record_type = data.get('record_type')
        if not record_type or record_type not in dict(AttendanceRecord.RECORD_TYPES):
            return JsonResponse({
                "success": False,
                "error": "Type de pointage invalide"
            }, status=400)
            
        # Vérifier que le type de pointage est cohérent avec le dernier état
        available_actions = get_available_actions(employee)
        valid_types = [action['value'] for action in available_actions]
        
        if record_type not in valid_types:
            return JsonResponse({
                "success": False,
                "error": f"Type de pointage '{record_type}' incohérent avec l'état actuel"
            }, status=400)
            
        # Créer l'enregistrement de pointage
        timestamp = timezone.now()
        attendance = AttendanceRecord.objects.create(
            employee=employee,
            record_type=record_type,
            timestamp=timestamp,
            location=data.get('location'),
            note=data.get('note')
        )
        
        # Obtenir la représentation du type de pointage
        record_type_display = dict(AttendanceRecord.RECORD_TYPES).get(record_type, record_type)
        
        # Obtenir le nom de l'employé
        user = employee.user
        employee_name = f"{user.first_name} {user.last_name}".strip() or user.username
        
        # Retourner les informations pour le popup de confirmation
        return JsonResponse({
            "success": True,
            "record_id": attendance.id,
            "timestamp": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            "record_type": record_type_display,
            "employee_name": employee_name,
            "available_actions": get_available_actions(employee)  # Retourne les nouvelles actions disponibles
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Format JSON invalide"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }, status=500)


def get_available_actions(employee):
    """
    Détermine les actions de pointage disponibles pour un employé 
    en fonction de son dernier enregistrement.
    """
    # Récupérer le dernier pointage de l'employé
    last_record = AttendanceRecord.objects.filter(
        employee=employee
    ).order_by('-timestamp').first()
    
    # Définir les actions disponibles en fonction du dernier état
    if not last_record or last_record.record_type == 'OUT':
        # Si pas de pointage ou dernier = sortie, seule l'entrée est possible
        return [{
            'value': 'IN',
            'label': 'Entrée (Clock In)',
            'description': 'Enregistrer votre arrivée'
        }]
    elif last_record.record_type == 'IN':
        # Si dernier = entrée, on peut sortir ou prendre une pause
        return [
            {
                'value': 'OUT',
                'label': 'Sortie (Clock Out)',
                'description': 'Enregistrer votre départ'
            },
            {
                'value': 'BREAK_START',
                'label': 'Début de Pause',
                'description': 'Commencer une pause'
            }
        ]
    elif last_record.record_type == 'BREAK_START':
        # Si dernier = début de pause, seule la fin de pause est possible
        return [{
            'value': 'BREAK_END',
            'label': 'Fin de Pause',
            'description': 'Terminer votre pause'
        }]
    elif last_record.record_type == 'BREAK_END':
        # Si dernier = fin de pause, on peut sortir ou reprendre une pause
        return [
            {
                'value': 'OUT',
                'label': 'Sortie (Clock Out)',
                'description': 'Enregistrer votre départ'
            },
            {
                'value': 'BREAK_START',
                'label': 'Début de Pause',
                'description': 'Commencer une nouvelle pause'
            }
        ]
    
    # Par défaut, autoriser toutes les actions (ne devrait pas arriver)
    return [
        {'value': 'IN', 'label': 'Entrée (Clock In)', 'description': 'Enregistrer votre arrivée'},
        {'value': 'OUT', 'label': 'Sortie (Clock Out)', 'description': 'Enregistrer votre départ'},
        {'value': 'BREAK_START', 'label': 'Début de Pause', 'description': 'Commencer une pause'},
        {'value': 'BREAK_END', 'label': 'Fin de Pause', 'description': 'Terminer votre pause'}
    ]