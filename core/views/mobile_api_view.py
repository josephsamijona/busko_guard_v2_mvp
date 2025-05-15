from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings

from ..serializers import EmployeeProfileSerializer, LoginSerializer
from ..models import Employee

import qrcode
from io import BytesIO
import base64

class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'obtention de token JWT"""
    pass  # Utilise le comportement par défaut de TokenObtainPairView

class CustomTokenRefreshView(TokenRefreshView):
    """Vue personnalisée pour le rafraîchissement de token JWT"""
    pass  # Utilise le comportement par défaut de TokenRefreshView

class LoginAPIView(APIView):
    """API pour la connexion et l'obtention des tokens"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                refresh = RefreshToken.for_user(user)
                
                # Vérifier si l'utilisateur a un profil employé
                has_employee_profile = hasattr(user, 'employee_profile')
                
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_id': user.id,
                    'username': user.username,
                    'is_staff': user.is_staff,
                    'has_employee_profile': has_employee_profile
                }
                
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Identifiants invalides'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutAPIView(APIView):
    """API pour la déconnexion (invalidation du token refresh)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()  # Ajoute le token à la blacklist
            
            return Response(
                {'message': 'Déconnexion réussie'}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class EmployeeProfileAPIView(APIView):
    """API pour récupérer le profil de l'employé connecté avec QR code"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier si l'utilisateur a un profil employé
        if not hasattr(request.user, 'employee_profile'):
            return Response(
                {'error': 'Profil employé non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        employee = request.user.employee_profile
        
        # Génération du QR code en base64
        qr_image_url = None
        if employee.qr_code:
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
        
        # Sérialiser les données
        serializer = EmployeeProfileSerializer(employee)
        data = serializer.data
        data['qr_code_image'] = qr_image_url
        
        return Response(data, status=status.HTTP_200_OK)