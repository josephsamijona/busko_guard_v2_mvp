import os

# Définir la structure du système de fichiers
structure = {
    "lib": {
        "main.dart": "",
        "constants.dart": "",
        "services": {
            "auth_service.dart": ""
        },
        "screens": {
            "login_screen.dart": "",
            "employee_profile_screen.dart": ""
        },
        "models": {
            "employee.dart": ""
        }
    }
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):  # dossier
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:  # fichier
            with open(path, 'w') as f:
                f.write(content)

# Créer la structure dans le dossier courant
create_structure('.', structure)
print("Structure de fichiers créée avec succès.")
