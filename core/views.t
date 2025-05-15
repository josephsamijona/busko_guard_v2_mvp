from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
import json
from .models import Employee,AttendanceRecord
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect




########################kiosk view
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Vue simple pour s'assurer que le client a un token CSRF.
    Cette vue sera appelée au chargement de la page kiosque.
    """
    return JsonResponse({"success": True})

@require_POST
def authenticate_qr_code(request):
    """
    API pour authentifier un employé via un code QR.
    Reçoit le code QR scanné et renvoie les informations de l'employé correspondant.
    """
    try:
        # Récupérer les données du corps de la requête
        data = json.loads(request.body)
        qr_code = data.get('qr_code')
        
        if not qr_code:
            return JsonResponse({
                "success": False,
                "message": "Code QR manquant dans la requête"
            }, status=400)  # Bad Request
        
        # Rechercher l'employé par QR code
        employee = Employee.objects.filter(qr_code=qr_code).select_related('user', 'department', 'role').first()
        
        if not employee or not employee.user.is_active:
            return JsonResponse({
                "success": False,
                "message": "Employé non reconnu ou inactif"
            }, status=404)  # Not Found
        
        # Formater les données de l'employé pour la réponse
        employee_data = {
            "id": str(employee.pk),
            "employee_id": employee.employee_id,
            "name": f"{employee.user.first_name} {employee.user.last_name}",
            "department": employee.department.name if employee.department else "",
            "role": employee.role.name if employee.role else ""
        }
        
        return JsonResponse({
            "success": True,
            "employee": employee_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Format de données invalide"
        }, status=400)  # Bad Request
        
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Erreur lors de l'authentification QR: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": "Une erreur est survenue lors du traitement"
        }, status=500)  # Internal Server Error
        
        
@require_POST
def authenticate_nfc(request):
    """
    API pour authentifier un employé via un badge NFC.
    Reçoit l'identifiant NFC scanné et renvoie les informations de l'employé correspondant.
    """
    try:
        # Récupérer les données du corps de la requête
        data = json.loads(request.body)
        nfc_id = data.get('nfc_id')
        
        if not nfc_id:
            return JsonResponse({
                "success": False,
                "message": "Identifiant NFC manquant dans la requête"
            }, status=400)  # Bad Request
        
        # Rechercher l'employé par identifiant NFC
        employee = Employee.objects.filter(nfc_id=nfc_id).select_related('user', 'department', 'role').first()
        
        if not employee or not employee.user.is_active:
            return JsonResponse({
                "success": False,
                "message": "Badge NFC non reconnu ou employé inactif"
            }, status=404)  # Not Found
        
        # Formater les données de l'employé pour la réponse
        employee_data = {
            "id": str(employee.pk),
            "employee_id": employee.employee_id,
            "name": f"{employee.user.first_name} {employee.user.last_name}",
            "department": employee.department.name if employee.department else "",
            "role": employee.role.name if employee.role else ""
        }
        
        return JsonResponse({
            "success": True,
            "employee": employee_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Format de données invalide"
        }, status=400)  # Bad Request
        
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Erreur lors de l'authentification NFC: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": "Une erreur est survenue lors du traitement"
        }, status=500)  # Internal Server Error
        
        
@ensure_csrf_cookie
def kiosk_view(request):
    """
    Vue principale du kiosque de pointage des présences.
    Affiche l'interface avec les options QR et NFC.
    """
    # Configuration JavaScript pour le kiosque
    js_config = {
        'qrApiUrl': request.build_absolute_uri(reverse('authenticate_qr_code')),
        'nfcApiUrl': request.build_absolute_uri(reverse('authenticate_nfc')),
        'actionsApiUrl': request.build_absolute_uri(reverse('get_available_actions')),
        'recordApiUrl': request.build_absolute_uri(reverse('record_attendance')),
        'csrfToken': request.META.get('CSRF_COOKIE', '')
    }
    
    # Contexte pour le template
    context = {
        'current_date': timezone.now(),
        'js_config': js_config,
        
    }
    
    return render(request, 'kiosk.html', context)


@require_GET
def get_available_actions(request):
    """
    API qui détermine les actions autorisées pour un employé en fonction
    de son dernier pointage.
    
    Paramètres URL:
    - employee_id (requis): Identifiant unique de l'employé
    
    Logique des actions disponibles:
    - Aucun pointage ou dernier=OUT      → IN (entrée) uniquement
    - Dernier=IN ou BREAK_END           → OUT (sortie) et BREAK_START (début pause)
    - Dernier=BREAK_START               → BREAK_END (fin pause) uniquement
    
    Retourne:
    - JSON avec liste des actions disponibles
    """
    # Récupérer l'ID de l'employé depuis les paramètres GET
    employee_id = request.GET.get('employee_id')
    
    # Vérifier que l'ID est fourni
    if not employee_id:
        return JsonResponse({
            'success': False,
            'message': 'ID employé manquant dans la requête'
        }, status=400)
    
    try:
        # Récupérer l'employé correspondant
        employee = Employee.objects.get(employee_id=employee_id)
        
        # Récupérer le dernier pointage de l'employé pour aujourd'hui
        today = timezone.now().date()
        last_record = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date=today
        ).order_by('-timestamp').first()
        
        # Déterminer les actions disponibles en fonction du dernier pointage
        available_actions = []
        
        if not last_record or last_record.record_type == 'OUT':
            # Si pas de pointage ou dernier = sortie → seule l'entrée est possible
            available_actions = ['IN']
        elif last_record.record_type == 'IN' or last_record.record_type == 'BREAK_END':
            # Si dernier = entrée ou fin de pause → sortie ou début de pause possible
            available_actions = ['OUT', 'BREAK_START']
        elif last_record.record_type == 'BREAK_START':
            # Si dernier = début de pause → seule la fin de pause est possible
            available_actions = ['BREAK_END']
        
        # Préparer les données des actions avec étiquettes
        actions_with_labels = []
        labels = {
            'IN': 'Arrivée',
            'OUT': 'Départ',
            'BREAK_START': 'Début de pause',
            'BREAK_END': 'Fin de pause'
        }
        
        for action in available_actions:
            actions_with_labels.append({
                'code': action,
                'label': labels.get(action, action)
            })
        
        # Retourner la liste des actions disponibles
        return JsonResponse({
            'success': True,
            'available_actions': available_actions,
            'available_actions_with_labels': actions_with_labels
        })
    
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employé non trouvé'
        }, status=404)
    
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Erreur lors de la détermination des actions disponibles: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Une erreur est survenue lors du traitement'
        }, status=500)
        
@csrf_protect
@require_POST
def record_attendance(request):
    """
    API pour enregistrer un nouveau pointage dans le système.
    
    Requête attendue (JSON):
    {
        "employee_id": "12345",        # Identifiant unique de l'employé
        "record_type": "IN",           # Type de pointage: IN, OUT, BREAK_START, BREAK_END
        "location": "Accueil"          # Optionnel: Lieu du pointage
    }
    
    Retourne:
    - Informations sur le pointage créé en cas de succès
    - Message d'erreur approprié en cas d'échec
    """
    try:
        # Récupérer et parser les données JSON
        data = json.loads(request.body)
        
        # Valider les champs requis
        employee_id = data.get('employee_id')
        record_type = data.get('record_type')
        location = data.get('location', '')  # Optionnel
        note = data.get('note', '')          # Optionnel
        
        if not employee_id or not record_type:
            return JsonResponse({
                'success': False,
                'message': 'Données incomplètes: ID employé et type de pointage requis'
            }, status=400)
        
        # Vérifier que le type de pointage est valide
        valid_types = [choice[0] for choice in AttendanceRecord.RECORD_TYPES]
        if record_type not in valid_types:
            return JsonResponse({
                'success': False,
                'message': f'Type de pointage invalide. Types autorisés: {", ".join(valid_types)}'
            }, status=400)
        
        # Récupérer l'employé
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Employé non trouvé'
            }, status=404)
        
        # Vérification supplémentaire: s'assurer que ce type de pointage est logique
        # par rapport au dernier pointage de l'employé (sécurité additionnelle)
        today = timezone.now().date()
        last_record = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date=today
        ).order_by('-timestamp').first()
        
        is_allowed = True
        error_message = ""
        
        if record_type == 'IN' and last_record and last_record.record_type == 'IN':
            is_allowed = False
            error_message = "Une entrée a déjà été enregistrée sans sortie correspondante"
        elif record_type == 'OUT' and (not last_record or last_record.record_type in ['OUT', 'BREAK_START']):
            is_allowed = False
            error_message = "Impossible d'enregistrer une sortie sans entrée préalable"
        elif record_type == 'BREAK_START' and (not last_record or last_record.record_type in ['OUT', 'BREAK_START']):
            is_allowed = False
            error_message = "Impossible de débuter une pause sans entrée préalable"
        elif record_type == 'BREAK_END' and (not last_record or last_record.record_type != 'BREAK_START'):
            is_allowed = False
            error_message = "Impossible de terminer une pause sans l'avoir débutée"
        
        if not is_allowed:
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)
        
        # Créer l'enregistrement de pointage
        timestamp = timezone.now()
        new_record = AttendanceRecord.objects.create(
            employee=employee,
            timestamp=timestamp,
            record_type=record_type,
            location=location,
            note=note
        )
        
        # Préparer les informations de réponse
        record_type_display = dict(AttendanceRecord.RECORD_TYPES).get(record_type)
        
        # Retourner les détails du pointage créé
        return JsonResponse({
            'success': True,
            'message': 'Pointage enregistré avec succès',
            'record': {
                'id': new_record.id,
                'employee_name': f"{employee.user.first_name} {employee.user.last_name}",
                'record_type': record_type,
                'record_type_display': record_type_display,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_date': timestamp.strftime('%d/%m/%Y'),
                'timestamp_time': timestamp.strftime('%H:%M:%S'),
                'location': location,
                'note': note
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Format de données invalide: JSON attendu'
        }, status=400)
        
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Erreur lors de l'enregistrement du pointage: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Une erreur est survenue lors du traitement'
        }, status=500)
        
        
        
###############_loginandlogoutview