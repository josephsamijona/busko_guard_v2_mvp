# BuskoGuard

<div align="center">
  <img src="static/img/buskoguard_logo.png" alt="BuskoGuard Logo" width="200"/>
  <h3>Système de gestion de contrôle de présence par QR Code et NFC</h3>
</div>

## 📋 Description

BuskoGuard est un système de contrôle de présence et de gestion d'employés qui utilise les technologies QR Code et NFC. Conçu comme une solution simple et non sophistiquée, ce projet vise à être facilement déployable et portable.

Le projet est né d'une observation personnelle à l'ISTEAH, où l'administration utilisait un système d'appointage manuel. BuskoGuard transforme ce processus manuel en un système numérique léger et accessible, adaptable aux ressources disponibles.

## ✨ Fonctionnalités

- **Automatisation du processus de pointage** des présences
- **Double technologie d'identification**: QR Codes et NFC
- **Interface Kiosk** pour effectuer les scans
- **Interface d'administration** pour la gestion des employés, départements et présences
- **Application mobile** servant de carte d'identité numérique
- **Consultation d'historique** des présences pour les employés
- **Gestion de congés** intégrée
- **Génération de rapports** en temps réel

## 🛠️ Technologies utilisées

### Backend
- **Django** (framework Python)
- **Django REST Framework** pour l'API
- **SQLite** (développement local) / **MySQL** (production)
- **JWT** pour l'authentification

### Frontend
- **Templates Django** avec Bootstrap
- **JavaScript** pour les fonctionnalités interactives

### Application mobile
- **Flutter** (framework Dart)
- **HTTP** pour les appels API

### Déploiement
- **Docker** pour la conteneurisation
- **Railway** pour le déploiement cloud (recommandé)

## 📥 Installation

### Prérequis
- Python 3.x
- Git
- Flutter (pour l'application mobile)

### Déploiement en local

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/josephsamijona/busko_guard_v2_mvp.git
   cd busko_guard_v2_mvp
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   
   # Sur Windows avec PowerShell ou Terminal
   .\venv\Scripts\activate
   
   # Sur Linux/Mac
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Créer un fichier .env**
   Créez un fichier `.env` à la racine du projet avec le contenu adéquat (voir documentation complète pour les détails).

5. **Appliquer les migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```

### Déploiement avec Docker

Voir la section déploiement de la documentation complète pour les instructions détaillées sur:
- Déploiement sur VPS
- Déploiement sur Raspberry Pi
- Déploiement sur Railway (recommandé)

## 🗂️ Structure du projet

```
buskoguard_v2_mvp/
├── manage.py
├── Dockerfile, runtime.txt, .env, Procfile, entrypoint.sh
├── requirements.txt
├── populate_db.py
├── config/
│   └── (fichiers de configuration Django)
├── core/
│   ├── admin.py
│   ├── models.py
│   ├── views/
│   │   ├── employee_view.py
│   │   ├── kiosk_view.py
│   │   └── mobile_api_view.py
│   ├── serializers/
│   └── utils/
│       └── generate_qr_code.py
├── templates/
├── static/
│   └── js/
│       ├── qrcodescanner.js
│       └── NFCReader.js
└── employee_mobile_app/
    └── lib/
        ├── main.dart
        ├── constants.dart
        ├── services/
        │   └── authservice.dart
        ├── models/
        │   └── employee.dart
        └── screens/
            ├── loginscreen.dart
            └── employee_profilescreen.dart
```

## 📱 Utilisation

### Interfaces disponibles

- **Interface Kiosk**: `http://127.0.0.1:8000/` - Pour effectuer les scans de présence
- **Interface Admin**: `http://127.0.0.1:8000/admin/` - Pour gérer les employés, départements, etc.
- **Interface Employé**: `http://127.0.0.1:8000/login/` - Pour l'accès des employés à leur carte ID et historique

### Configuration de l'application mobile

1. Naviguez vers le dossier de l'application mobile
   ```bash
   cd employee_mobile_app
   ```

2. Installez les packages
   ```bash
   flutter pub get
   ```

3. Mettez à jour l'URL API dans `lib/constants.dart`
   ```dart
   const String baseUrl = 'http://127.0.0.1:8000';  // Ou l'URL de votre déploiement
   ```

4. Lancez l'application en mode debug ou créez un APK
   ```bash
   flutter run
   # Ou pour créer un APK
   flutter build apk --release
   ```

## 🏗️ Architecture

BuskoGuard fonctionne selon une architecture simple:

1. **Système monolithique Django** qui gère:
   - Interface administrateur
   - Interface kiosk
   - API REST
   - Système d'authentification

2. **Application mobile Flutter** qui sert de:
   - Carte d'identité numérique
   - Interface de consultation

3. **Base de données** avec les modèles principaux:
   - Department: Départements de l'entreprise
   - Role: Postes ou fonctions
   - User: Extension du modèle Django User
   - Employee: Informations professionnelles
   - Schedule: Horaires planifiés
   - AttendanceRecord: Enregistrements des pointages
   - LeaveRequest: Demandes de congés

## 🔮 Perspectives d'évolution

### Améliorations fonctionnelles
- Tableau de bord analytique
- Système de notification avancé
- Gestion des horaires flexible

### Extensions possibles
- Module de gestion du temps complet
- Extension vers la gestion RH
- Contrôle d'accès physique
- Support multi-site

### Technologies futures
- Biométrie (reconnaissance faciale, empreintes)
- Géolocalisation intelligente
- Intelligence artificielle pour l'optimisation
- Intégration avec les systèmes d'entreprise

## 👤 Auteur

**Joseph Samuel Jonathan**
- Étudiant en 4ème année de génie informatique
- Institut des Sciences, des Technologies et des Études Avancées d'Haïti (ISTEAH)

## 📝 Licence

Ce projet est sous licence [MIT](LICENSE).

---

<div align="center">
  <p>Développé dans le cadre du projet d'intégration des connaissances en mathématique et informatique (INF5000)</p>
  <p>© 2024 Joseph Samuel Jonathan - ISTEAH</p>
</div>