#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de population de la base de données pour une application générique.
Crée:
- Départements
- Rôles
- Utilisateurs & Employés (avec identifiants NFC et QR codes)
- Horaires de travail
- Enregistrements de présence
- Demandes de congé
ET EXPORTE LES IDENTIFIANTS UTILISATEURS DANS UN FICHIER JSON.
"""

import os
import sys
import django
import random
import string
import json # Ajout de l'import pour la gestion JSON
from datetime import datetime, timedelta, time
from django.utils import timezone

# Configuration de l'environnement Django
# Assurez-vous que 'votreprojet.settings' correspond à votre configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") # Gardé tel quel, ajustez si besoin
django.setup()

# Une fois Django configuré, on peut importer les modèles
from django.contrib.auth.models import Group

from core.models import Department, Role, User, Employee, Schedule, AttendanceRecord, LeaveRequest # Gardé tel quel

# Paramètres
NB_EMPLOYEES = 50 # Légèrement réduit pour l'exemple, vous pouvez l'augmenter
DAYS_OF_HISTORY = 40 # Nombre de jours d'historique pour les pointages et congés

# Liste pour stocker les identifiants des utilisateurs créés
user_credentials_list = []

def generate_random_string(length=5):
    """Génère une chaîne aléatoire de caractères alphanumériques."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_departments():
    """Création des départements (nouvelles données)"""
    print("\n--- Création des Départements ---")
    departments_data = [
        {"name": "Technologie & Innovation", "description": "Développement de solutions et R&D."},
        {"name": "Services Clientèle", "description": "Support et relations avec les clients."},
        {"name": "Opérations", "description": "Gestion des processus internes et logistique."},
        {"name": "Stratégie & Développement", "description": "Planification et croissance de l'entreprise."},
        {"name": "Ressources Humaines Globales", "description": "Gestion du personnel et culture d'entreprise."},
        {"name": "Finance & Administration", "description": "Comptabilité, budget et administration générale."}
    ]
    
    created_departments = []
    for dept_data in departments_data:
        department, created = Department.objects.get_or_create(
            name=dept_data["name"], 
            defaults={"description": dept_data["description"]}
        )
        created_departments.append(department)
        print(f"Département {'créé' if created else 'existant'}: {department.name}")
    
    return created_departments

def create_roles():
    """Création des rôles (nouvelles données)"""
    print("\n--- Création des Rôles ---")
    roles_data = [
        {"name": "Chef d'Équipe", "description": "Dirige et supervise une équipe."},
        {"name": "Spécialiste Senior", "description": "Expertise technique ou fonctionnelle avancée."},
        {"name": "Coordinateur de Projet", "description": "Gère la coordination des projets."},
        {"name": "Analyste de Données", "description": "Analyse les données pour aider à la décision."},
        {"name": "Consultant Fonctionnel", "description": "Conseille sur les aspects fonctionnels des solutions."},
        {"name": "Chargé de Support", "description": "Fournit une assistance technique ou client."},
        {"name": "Développeur Full-Stack", "description": "Développe les parties front-end et back-end."},
        {"name": "Administrateur Système", "description": "Gère l'infrastructure informatique."}
    ]
    
    created_roles = []
    for role_data_item in roles_data:
        role, created = Role.objects.get_or_create(
            name=role_data_item["name"], 
            defaults={"description": role_data_item["description"]}
        )
        created_roles.append(role)
        print(f"Rôle {'créé' if created else 'existant'}: {role.name}")
    
    return created_roles

def create_users_and_employees(departments, roles):
    """Création des utilisateurs et des employés associés (nouvelles données)"""
    print("\n--- Création des Utilisateurs et Employés ---")
    # Nouvelles listes de prénoms et noms
    first_names = [
        "Alexandre", "Léa", "Lucas", "Chloé", "Gabriel", "Manon", "Adam", "Camille",
        "Raphaël", "Emma", "Hugo", "Louise", "Arthur", "Jade", "Louis", "Alice",
        "Jules", "Lina", "Ethan", "Rose", "Victor", "Anna", "Paul", "Ambre"
    ]
    
    last_names = [
        "Bernard", "Garcia", "Robert", "Petit", "Dubois", "Moreau", "Laurent", "Simon",
        "Michel", "Lefevre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier",
        "Girard", "Bonnet", "Vincent", "Lambert", "Fontaine", "Rousseau", "Blanc", "Henry"
    ]

    # Nouveaux noms de rues et villes
    street_names = ["de l'Avenir", "des Étoiles", "de l'Innovation", "Principale", "du Progrès"]
    cities = ["Innoville", "Techburg", "Portail-Ville", "Nova Cité", "Futurix"]
    
    created_employees = []
    # Création d'un groupe "Superviseurs" au lieu de "Administrateurs" pour varier
    supervisor_group, _ = Group.objects.get_or_create(name="Superviseurs")
    
    # Création d'un utilisateur admin spécifique si vous en avez besoin pour des tests
    admin_user, admin_created = User.objects.get_or_create(
        username="admin_global",
        defaults={
            "first_name": "Admin",
            "last_name": "Principal",
            "email": "admin@newcorp.com",
            "is_staff": True,
            "is_superuser": True, # Superutilisateur
            "date_of_birth": datetime.now().date() - timedelta(days=random.randint(10000, 15000)),
            "phone_number": "0123456789",
        }
    )
    if admin_created:
        admin_password = "adminpassword123" # Mot de passe pour l'admin
        admin_user.set_password(admin_password)
        admin_user.save()
        print(f"Utilisateur Super Admin {'créé'}: {admin_user.username}")
        # Ajout des identifiants de l'admin à la liste
        user_credentials_list.append({"username": admin_user.username, "password": admin_password})


    for i in range(NB_EMPLOYEES):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        # Changement du domaine email
        username = f"{first_name.lower().replace('é','e').replace('ê','e')}.{last_name.lower()}{random.randint(1, 99)}"
        email = f"{username}@newcorp.com" # Nouveau domaine email
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "is_staff": random.random() < 0.15, # 15% sont staff
                "date_of_birth": datetime.now().date() - timedelta(days=random.randint(7000, 22000)),
                "phone_number": f"0{random.randint(6, 7)}{''.join(random.choices(string.digits, k=8))}",
                "address": f"{random.randint(1, 200)} Avenue {random.choice(street_names)}, {random.randint(10000, 95000)} {random.choice(cities)}"
            }
        )
        
        default_password = "password123" # Gardons un mot de passe par défaut simple pour les tests

        if created:
            user.set_password(default_password)
            user.save()
            
            # Ajout des identifiants à la liste pour l'export JSON
            user_credentials_list.append({"username": username, "password": default_password})
            
            if user.is_staff and random.random() < 0.7: # 70% des staff sont superviseurs
                user.groups.add(supervisor_group)
                user.save()
        
        try:
            employee = user.employee_profile
            employee_created_flag = False
        except Employee.DoesNotExist:
            employee_id = f"EMP{random.randint(10000, 99999)}"
            nfc_id = generate_random_string(8) # ID NFC un peu plus long
            qr_code_data = f"USER:{username};ID:{employee_id}" # Données pour le QR code
            
            employee = Employee.objects.create(
                user=user,
                employee_id=employee_id,
                department=random.choice(departments),
                role=random.choice(roles),
                nfc_id=nfc_id,
                qr_code=qr_code_data
            )
            employee_created_flag = True
        
        created_employees.append(employee)
        print(f"Employé {'créé' if employee_created_flag else 'existant'}: {employee.user.get_full_name()} ({employee.employee_id})")
    
    return created_employees

def create_schedules(employees):
    """Création des horaires de travail pour les employés (logique similaire, données de temps gardées)"""
    print("\n--- Création des Horaires ---")
    schedule_templates = [
        {"start_time": time(9, 0), "end_time": time(17, 30), "break_start": time(12, 30), "break_end": time(13, 30)},
        {"start_time": time(8, 0), "end_time": time(16, 0), "break_start": time(12, 0), "break_end": time(12, 45)},
        {"start_time": time(10, 0), "end_time": time(18, 30), "break_start": time(13, 0), "break_end": time(13, 45)},
        {"start_time": time(8, 30), "end_time": time(17, 0), "break_start": None, "break_end": None} # Journée continue
    ]
    
    schedules_created_count = 0
    
    for employee in employees:
        for day in range(7): # 0=Lundi, 6=Dimanche
            if day >= 5 and random.random() < 0.6: # 60% de chance de ne pas travailler le weekend
                continue
                
            template = random.choice(schedule_templates)
            
            schedule, created = Schedule.objects.get_or_create(
                employee=employee,
                day_of_week=day,
                defaults={
                    "start_time": template["start_time"],
                    "end_time": template["end_time"],
                    "break_start": template["break_start"],
                    "break_end": template["break_end"]
                }
            )
            if created:
                schedules_created_count += 1
    
    print(f"{schedules_created_count} horaires de travail créés au total.")

def create_attendance_records(employees):
    """Création des enregistrements de pointage (logique similaire, données de lieux modifiées)"""
    print("\n--- Création des Enregistrements de Présence ---")
    # Nouveaux lieux
    locations = ['Siège Social', 'Bureau Satellite Alpha', 'Client Z', 'À Distance', 'Espace Co-working']
    
    records_created_count = 0
    
    for day_offset in range(DAYS_OF_HISTORY, 0, -1):
        current_date_val = timezone.now().date() - timedelta(days=day_offset)
        
        if current_date_val.weekday() >= 5 and random.random() < 0.8: # Moins de pointages le weekend
            continue 
            
        for employee in employees:
            if random.random() < 0.08: # 8% de chance d'absence
                continue
            
            try:
                schedule = Schedule.objects.get(employee=employee, day_of_week=current_date_val.weekday())
            except Schedule.DoesNotExist:
                continue 
            
            # Entrée
            entry_time_dt = datetime.combine(current_date_val, schedule.start_time)
            entry_time_dt = timezone.make_aware(entry_time_dt) + timedelta(minutes=random.randint(-15, 15))
            AttendanceRecord.objects.create(employee=employee, timestamp=entry_time_dt, record_type='IN', location=random.choice(locations))
            records_created_count += 1
            
            # Pauses
            if schedule.break_start and schedule.break_end and random.random() < 0.9: # 90% prennent leur pause
                break_start_dt = datetime.combine(current_date_val, schedule.break_start)
                break_start_dt = timezone.make_aware(break_start_dt) + timedelta(minutes=random.randint(-5, 5))
                AttendanceRecord.objects.create(employee=employee, timestamp=break_start_dt, record_type='BREAK_START')
                records_created_count += 1
                
                break_end_dt = datetime.combine(current_date_val, schedule.break_end)
                break_end_dt = timezone.make_aware(break_end_dt) + timedelta(minutes=random.randint(-5, 5))
                AttendanceRecord.objects.create(employee=employee, timestamp=break_end_dt, record_type='BREAK_END')
                records_created_count += 1
            
            # Sortie
            exit_time_dt = datetime.combine(current_date_val, schedule.end_time)
            exit_time_dt = timezone.make_aware(exit_time_dt) + timedelta(minutes=random.randint(-10, 20))
            AttendanceRecord.objects.create(employee=employee, timestamp=exit_time_dt, record_type='OUT', location=random.choice(locations))
            records_created_count += 1
            
    print(f"{records_created_count} enregistrements de pointage créés au total.")

def create_leave_requests(employees):
    """Création des demandes de congé (logique similaire)"""
    print("\n--- Création des Demandes de Congé ---")
    leave_types_options = ['VACATION', 'SICK', 'PERSONAL', 'OTHER']
    statuses_options = ['PENDING', 'APPROVED', 'REJECTED']
    status_weights_options = [0.2, 0.7, 0.1] # Plus d'approuvées
    
    # Utiliser des employés avec un rôle de "Chef d'Équipe" ou "Superviseurs" (du groupe) pour approuver
    potential_approvers = [
        emp for emp in employees 
        if emp.role.name == "Chef d'Équipe" or \
           emp.user.groups.filter(name="Superviseurs").exists()
    ]
    if not potential_approvers: # Au cas où aucun manager/superviseur n'est généré
        potential_approvers = employees # N'importe quel employé peut approuver si aucun manager trouvé

    requests_created_count = 0
    
    for employee in employees:
        nb_requests_to_create = random.randint(0, 2) # Moins de demandes par employé
        
        for _ in range(nb_requests_to_create):
            leave_type_choice = random.choice(leave_types_options)
            
            request_offset_days = random.randint(-DAYS_OF_HISTORY + 5, 50) # Demandes passées et futures
            start_date_val = timezone.now().date() + timedelta(days=request_offset_days)
            duration_days = random.randint(1, 10)
            end_date_val = start_date_val + timedelta(days=duration_days -1)
            
            # S'assurer que la date de demande est avant la date de début du congé
            request_date_dt = timezone.make_aware(datetime.combine(
                start_date_val - timedelta(days=random.randint(2,30)), # Demandé entre 2 et 30 jours avant
                time(random.randint(8,17), random.randint(0,59))
            ))
            
            status_choice = random.choices(statuses_options, weights=status_weights_options, k=1)[0]
            
            response_by_user = None
            response_date_val = None
            
            if status_choice != 'PENDING':
                if potential_approvers:
                    response_by_user = random.choice(potential_approvers)
                # S'assurer que la date de réponse est entre la demande et le début du congé (ou après si approuvé/rejeté tardivement)
                days_for_response = random.randint(1, (start_date_val - request_date_dt.date()).days -1 if (start_date_val - request_date_dt.date()).days > 1 else 1)
                response_date_val = request_date_dt + timedelta(days=days_for_response, hours=random.randint(1,8))


            LeaveRequest.objects.create(
                employee=employee,
                start_date=start_date_val,
                end_date=end_date_val,
                leave_type=leave_type_choice,
                reason=f"Demande pour {dict(LeaveRequest.LEAVE_TYPES)[leave_type_choice].lower()} par {employee.user.get_full_name()}.",
                status=status_choice,
                request_date=request_date_dt,
                response_date=response_date_val,
                response_by=response_by_user 
            )
            requests_created_count += 1
            
    print(f"{requests_created_count} demandes de congé créées au total.")

def export_credentials_to_json(filename="user_credentials.json"):
    """Exporte la liste des identifiants utilisateurs dans un fichier JSON."""
    print(f"\n--- Exportation des identifiants utilisateurs vers {filename} ---")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(user_credentials_list, f, ensure_ascii=False, indent=4)
        print(f"Les identifiants de {len(user_credentials_list)} utilisateurs ont été sauvegardés dans {filename}")
    except IOError:
        print(f"Erreur : Impossible d'écrire dans le fichier {filename}")

def main():
    """Fonction principale"""
    print("Début du processus de population de la base de données (nouvelles données)...")
    
    departments_list = create_departments()
    roles_list = create_roles()
    employees_list = create_users_and_employees(departments_list, roles_list)
    create_schedules(employees_list)
    create_attendance_records(employees_list)
    create_leave_requests(employees_list)
    
    # Nouvelle étape : exporter les identifiants
    export_credentials_to_json()
    
    print("\nPopulation de la base de données et exportation des identifiants terminées avec succès!")

if __name__ == "__main__":
    main()