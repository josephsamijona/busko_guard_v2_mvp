from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Employee, Department, Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle User personnalisé"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_of_birth', 
                  'phone_number', 'address', 'profile_picture']
        read_only_fields = ['id']

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Department"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']

class RoleSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Role"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Serializer pour afficher le profil complet d'un employé"""
    # Inclusion des données utilisateur
    user = UserSerializer(read_only=True)
    
    # Inclusion des données de département et rôle (au lieu des IDs)
    department = DepartmentSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    
    # Champ pour le nom complet (calculé)
    full_name = serializers.SerializerMethodField()
    
    # Champ pour l'image QR code (géré au niveau de la vue)
    qr_code_image = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = Employee
        fields = ['employee_id', 'user', 'department', 'role', 'nfc_id', 
                  'qr_code', 'qr_code_image', 'full_name']
    
    def get_full_name(self, obj):
        """Méthode pour obtenir le nom complet de l'employé"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

class LoginSerializer(serializers.Serializer):
    """Serializer pour l'authentification"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)