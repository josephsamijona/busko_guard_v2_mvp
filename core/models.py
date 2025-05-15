# Fichier : models.py
#
# Description : Ce fichier définit les modèles de données pour l'application,
#               représentant la structure de la base de données et les relations
#               entre les différentes entités (Départements, Rôles, Utilisateurs,
#               Employés, Horaires, Pointages, Demandes de Congé).

# Importations nécessaires de Django
from django.db import models  # Module de base pour la création de modèles
from django.contrib.auth.models import AbstractUser  # Classe de base pour un modèle User personnalisable
from django.utils import timezone  # Utilitaires pour la gestion des dates et heures
from django.conf import settings  # Pour accéder aux configurations du projet, notamment AUTH_USER_MODEL

# --- Section 1: Modèles de base pour l'organisation ---

class Department(models.Model):
    """
    Modèle représentant un département au sein de l'entreprise.
    Chaque employé peut être associé à un département.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du département",
        help_text="Le nom officiel du département (ex: 'Ressources Humaines', 'Informatique')."
    )
    description = models.TextField(
        blank=True,  # Le champ peut être vide dans les formulaires
        null=True,   # Le champ peut être NULL dans la base de données
        verbose_name="Description",
        help_text="Description facultative des responsabilités ou objectifs du département."
    )

    def __str__(self):
        """
        Représentation textuelle de l'objet Department.
        Utilisée principalement dans l'interface d'administration Django.
        Retourne :
            str: Le nom du département.
        """
        return self.name

class Role(models.Model):
    """
    Modèle représentant un rôle ou un poste au sein de l'entreprise.
    Chaque employé peut être associé à un rôle spécifique.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du rôle",
        help_text="L'intitulé du poste (ex: 'Développeur Senior', 'Chef de projet')."
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description facultative des responsabilités ou compétences associées à ce rôle."
    )

    def __str__(self):
        """
        Représentation textuelle de l'objet Role.
        Retourne :
            str: Le nom du rôle.
        """
        return self.name

# --- Section 2: Modèle Utilisateur personnalisé ---

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé étendant AbstractUser de Django.
    Ce modèle gère l'authentification (identifiant, mot de passe) et les informations
    personnelles de base de l'utilisateur. Il est conçu pour être lié
    au modèle Employee via une relation OneToOne.

    Champs hérités d'AbstractUser :
    - username (identifiant unique)
    - first_name (prénom)
    - last_name (nom de famille)
    - email
    - password (hashé)
    - groups (pour les groupes de permissions)
    - user_permissions (pour les permissions spécifiques)
    - is_staff (accès à l'interface d'administration)
    - is_active (statut de l'utilisateur)
    - is_superuser (super-utilisateur avec toutes les permissions)
    - last_login (dernière connexion)
    - date_joined (date de création du compte)
    """
    # Informations personnelles supplémentaires
    date_of_birth = models.DateField(
        verbose_name="Date de naissance",
        null=True,
        blank=True,
        help_text="Date de naissance de l'utilisateur."
    )
    phone_number = models.CharField(
        verbose_name="Numéro de téléphone",
        max_length=20,  # Augmenté pour plus de flexibilité (indicatifs internationaux)
        blank=True,
        null=True,
        help_text="Numéro de téléphone de contact de l'utilisateur."
    )
    address = models.TextField(
        verbose_name="Adresse",
        blank=True,
        null=True,
        help_text="Adresse postale de l'utilisateur."
    )
    profile_picture = models.ImageField(
        verbose_name="Photo de profil",
        upload_to='profile_pics/',  # Chemin de stockage des images (relatif à MEDIA_ROOT)
        blank=True,
        null=True,
        help_text="Photo de profil de l'utilisateur."
    )
    # Exemple de champ supplémentaire (à décommenter et adapter si besoin) :
    # genre = models.CharField(
    #     max_length=10,
    #     choices=[('HOMME', 'Homme'), ('FEMME', 'Femme'), ('AUTRE', 'Autre')],
    #     blank=True,
    #     null=True,
    #     verbose_name="Genre"
    # )

    def __str__(self):
        """
        Représentation textuelle de l'objet User.
        Retourne le nom d'utilisateur par défaut, ou le nom complet si disponible.
        Retourne :
            str: Représentation de l'utilisateur.
        """
        full_name = self.get_full_name()
        return full_name if full_name else self.username

# --- Section 3: Modèle Employé ---

class Employee(models.Model):
    """
    Modèle représentant les informations spécifiques à un employé.
    Ce modèle est lié au modèle User personnalisé via une relation OneToOneField,
    séparant ainsi les préoccupations d'authentification (User) des données
    professionnelles (Employee).
    """
    # Relation OneToOne avec le modèle User personnalisé.
    # Chaque employé est un utilisateur, et chaque utilisateur peut (optionnellement) avoir un profil employé.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Référence dynamique au modèle User défini dans settings.py
        on_delete=models.CASCADE,  # Si l'objet User est supprimé, l'objet Employee associé l'est aussi.
        related_name='employee_profile',  # Permet d'accéder à l'employé depuis un objet User (ex: user.employee_profile)
        primary_key=True, # Fait de `user` la clé primaire de la table Employee. Simplifie les jointures.
        verbose_name="Utilisateur associé"
    )

    # Informations spécifiques à l'employé
    employee_id = models.CharField(
        verbose_name="ID Employé",
        max_length=20,
        unique=True,  # Assure que chaque ID employé est unique
        help_text="Identifiant unique de l'employé au sein de l'entreprise."
    )
    department = models.ForeignKey(
        Department,
        verbose_name="Département",
        on_delete=models.SET_NULL,  # Si le département est supprimé, le champ devient NULL (l'employé n'est pas supprimé)
        null=True,
        blank=True,
        help_text="Département auquel l'employé est rattaché."
    )
    role = models.ForeignKey(
        Role,
        verbose_name="Rôle",
        on_delete=models.SET_NULL, # Si le rôle est supprimé, le champ devient NULL
        null=True,
        blank=True,
        help_text="Rôle ou poste de l'employé."
    )
    nfc_id = models.CharField(
        verbose_name="ID NFC",
        max_length=100,
        unique=True, # Assure que chaque ID NFC est unique
        blank=True,
        null=True,
        help_text="Identifiant de la carte NFC de l'employé, si applicable."
    )
    qr_code = models.CharField(
        verbose_name="Code QR",
        max_length=255, # Peut stocker une URL ou des données encodées
        blank=True,
        null=True,
        help_text="Données du code QR de l'employé, si applicable."
    )

    # Remarque : Les champs tels que first_name, last_name, email, phone_number, address,
    # profile_picture, groups, user_permissions sont désormais gérés par le modèle User
    # et accessibles via `self.user` (ex: `self.user.first_name`).

    def __str__(self):
        """
        Représentation textuelle de l'objet Employee.
        Affiche le nom complet de l'utilisateur associé (via le modèle User)
        et l'ID de l'employé.
        Retourne :
            str: Représentation de l'employé.
        """
        # Accès sécurisé aux informations de l'utilisateur lié.
        # Avec primary_key=True sur le OneToOneField, self.user devrait toujours exister si l'objet Employee existe.
        user_display_name = f"{self.user.first_name} {self.user.last_name}".strip()
        if not user_display_name:  # Si prénom/nom ne sont pas définis, utilise le username
            user_display_name = self.user.username
        return f"{user_display_name} ({self.employee_id})"

# --- Section 4: Modèles liés à la gestion du temps et des présences ---

class Schedule(models.Model):
    """
    Modèle représentant l'horaire de travail d'un employé pour un jour spécifique de la semaine.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,  # Si l'employé est supprimé, ses horaires le sont aussi
        verbose_name="Employé",
        help_text="L'employé concerné par cet horaire."
    )
    DAY_CHOICES = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'),
        (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]
    day_of_week = models.IntegerField(
        choices=DAY_CHOICES,
        verbose_name="Jour de la semaine",
        help_text="Jour de la semaine pour cet horaire (0=Lundi, 6=Dimanche)."
    )
    start_time = models.TimeField(
        verbose_name="Heure de début",
        help_text="Heure à laquelle l'employé commence à travailler."
    )
    end_time = models.TimeField(
        verbose_name="Heure de fin",
        help_text="Heure à laquelle l'employé termine de travailler."
    )
    break_start = models.TimeField(
        verbose_name="Début de pause",
        null=True,
        blank=True,
        help_text="Heure de début de la pause (facultatif)."
    )
    break_end = models.TimeField(
        verbose_name="Fin de pause",
        null=True,
        blank=True,
        help_text="Heure de fin de la pause (facultatif)."
    )

    class Meta:
        # Contrainte d'unicité : un employé ne peut avoir qu'un seul horaire
        # défini pour un jour donné de la semaine.
        unique_together = ('employee', 'day_of_week')
        verbose_name = "Horaire"
        verbose_name_plural = "Horaires"

    def __str__(self):
        """
        Représentation textuelle de l'objet Schedule.
        Affiche le nom de l'employé, le jour de la semaine et les heures.
        Retourne :
            str: Représentation de l'horaire.
        """
        user_display_name = f"{self.employee.user.first_name} {self.employee.user.last_name}".strip()
        if not user_display_name:
            user_display_name = self.employee.user.username
        return f"{user_display_name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"

class AttendanceRecord(models.Model):
    """
    Modèle pour enregistrer les pointages des employés (entrées, sorties, pauses).
    """
    RECORD_TYPES = [
        ('IN', 'Entrée (Clock In)'),
        ('OUT', 'Sortie (Clock Out)'),
        ('BREAK_START', 'Début de Pause'),
        ('BREAK_END', 'Fin de Pause'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE, # Si l'employé est supprimé, ses pointages le sont aussi
        verbose_name="Employé",
        help_text="L'employé concerné par ce pointage."
    )
    timestamp = models.DateTimeField(
        default=timezone.now, # Date et heure actuelles par défaut lors de la création
        verbose_name="Horodatage",
        help_text="Date et heure exactes du pointage."
    )
    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPES,
        verbose_name="Type de pointage",
        help_text="Nature de l'enregistrement (entrée, sortie, début/fin de pause)."
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Lieu",
        help_text="Lieu du pointage (ex: 'Bureau principal', 'Client X') (facultatif)."
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note",
        help_text="Notes additionnelles concernant ce pointage (facultatif)."
    )

    class Meta:
        verbose_name = "Enregistrement de présence"
        verbose_name_plural = "Enregistrements de présence"
        ordering = ['-timestamp'] # Ordonner par défaut du plus récent au plus ancien

    def __str__(self):
        """
        Représentation textuelle de l'objet AttendanceRecord.
        Affiche le nom de l'employé, le type de pointage et l'horodatage.
        Retourne :
            str: Représentation du pointage.
        """
        user_display_name = f"{self.employee.user.first_name} {self.employee.user.last_name}".strip()
        if not user_display_name:
            user_display_name = self.employee.user.username
        return f"{user_display_name} - {self.get_record_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# --- Section 5: Modèle pour la gestion des congés ---

class LeaveRequest(models.Model):
    """
    Modèle pour gérer les demandes de congé des employés.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
    ]
    LEAVE_TYPES = [
        ('VACATION', 'Vacances'),
        ('SICK', 'Maladie'),
        ('PERSONAL', 'Personnel'),
        ('OTHER', 'Autre'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE, # Si l'employé est supprimé, ses demandes de congé le sont aussi
        verbose_name="Demandeur",
        related_name='leave_requests', # Pour accéder aux demandes depuis un objet Employé (employee.leave_requests)
        help_text="L'employé qui soumet la demande de congé."
    )
    start_date = models.DateField(
        verbose_name="Date de début",
        help_text="Date de début du congé demandé."
    )
    end_date = models.DateField(
        verbose_name="Date de fin",
        help_text="Date de fin du congé demandé."
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
        verbose_name="Type de congé",
        help_text="La nature du congé (Vacances, Maladie, etc.)."
    )
    reason = models.TextField(
        verbose_name="Motif",
        help_text="Explication ou motif de la demande de congé."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING', # Statut par défaut lors de la création
        verbose_name="Statut",
        help_text="Le statut actuel de la demande (En attente, Approuvé, Rejeté)."
    )
    request_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de la demande",
        help_text="Date et heure à laquelle la demande a été soumise."
    )
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de réponse",
        help_text="Date et heure à laquelle la demande a été traitée (approuvée/rejetée)."
    )
    # Employé qui a traité la demande (manager, RH)
    response_by = models.ForeignKey(
        Employee, # Référence un autre employé (le manager/RH)
        on_delete=models.SET_NULL, # Si l'employé traitant est supprimé, ce champ devient NULL
        null=True,
        blank=True,
        related_name='processed_leave_requests', # Pour accéder aux demandes traitées par cet employé (employee.processed_leave_requests)
        verbose_name="Traité par",
        help_text="L'employé (généralement un manager ou RH) qui a répondu à la demande."
    )

    class Meta:
        verbose_name = "Demande de congé"
        verbose_name_plural = "Demandes de congé"
        ordering = ['-request_date'] # Ordonner par défaut les demandes les plus récentes en premier

    def __str__(self):
        """
        Représentation textuelle de l'objet LeaveRequest.
        Affiche le nom de l'employé demandeur, le type de congé et les dates.
        Retourne :
            str: Représentation de la demande de congé.
        """
        user_display_name = f"{self.employee.user.first_name} {self.employee.user.last_name}".strip()
        if not user_display_name:
            user_display_name = self.employee.user.username
        return f"{user_display_name} - {self.get_leave_type_display()} ({self.start_date.strftime('%d/%m/%Y')} au {self.end_date.strftime('%d/%m/%Y')}) - Statut: {self.get_status_display()}"

# --- Instructions post-définition des modèles ---
# 
# Exécutez les commandes suivantes pour appliquer les modifications à la base de données :
# python manage.py makemigrations 
# python manage.py migrate