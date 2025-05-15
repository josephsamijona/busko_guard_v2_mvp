import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants.dart';
import '../models/employee.dart';

class AuthService extends ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _error;
  Employee? _employeeProfile;

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get error => _error;
  Employee? get employeeProfile => _employeeProfile;

  // Constructeur - vérifier si l'utilisateur est déjà connecté lors du lancement
  AuthService() {
    checkAuthStatus();
  }

  // Vérifier le statut d'authentification au démarrage
  Future<void> checkAuthStatus() async {
    _isLoading = true;
    notifyListeners();

    try {
      final accessToken = await _storage.read(key: StorageKeys.accessToken);
      if (accessToken != null) {
        _isAuthenticated = true;
        await fetchEmployeeProfile(); // Charger le profil si déjà connecté
      }
    } catch (e) {
      _error = e.toString();
      _isAuthenticated = false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Connexion
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse(ApiUrls.login),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        
        // Stocker les tokens et les informations utilisateur
        await _storage.write(key: StorageKeys.accessToken, value: data['access']);
        await _storage.write(key: StorageKeys.refreshToken, value: data['refresh']);
        await _storage.write(key: StorageKeys.userId, value: data['user_id'].toString());
        await _storage.write(key: StorageKeys.username, value: data['username']);
        await _storage.write(key: StorageKeys.isStaff, value: data['is_staff'].toString());
        await _storage.write(
          key: StorageKeys.hasEmployeeProfile, 
          value: data['has_employee_profile'].toString()
        );

        _isAuthenticated = true;
        
        // Si l'utilisateur a un profil employé, charger ce profil
        if (data['has_employee_profile'] == true) {
          await fetchEmployeeProfile();
        }
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        // Gérer les erreurs
        if (response.statusCode == 401) {
          _error = ErrorMessages.authFailed;
        } else {
          _error = ErrorMessages.serverError;
        }
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = ErrorMessages.networkError;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Déconnexion
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      final refreshToken = await _storage.read(key: StorageKeys.refreshToken);
      if (refreshToken != null) {
        final accessToken = await _storage.read(key: StorageKeys.accessToken);
        
        // Appeler l'API de déconnexion pour blacklister le token
        await http.post(
          Uri.parse(ApiUrls.logout),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $accessToken',
          },
          body: jsonEncode({
            'refresh': refreshToken,
          }),
        );
      }
    } catch (e) {
      // Ignorer les erreurs lors de la déconnexion côté serveur
      print('Erreur lors de la déconnexion: $e');
    } finally {
      // Effacer le stockage local quoi qu'il arrive
      await _storage.deleteAll();
      _isAuthenticated = false;
      _employeeProfile = null;
      _isLoading = false;
      notifyListeners();
    }
  }

  // Rafraîchir le token
  Future<bool> refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: StorageKeys.refreshToken);
      if (refreshToken == null) {
        return false;
      }

      final response = await http.post(
        Uri.parse(ApiUrls.refreshToken),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'refresh': refreshToken,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        await _storage.write(key: StorageKeys.accessToken, value: data['access']);
        return true;
      } else {
        // Si le rafraîchissement échoue, forcer la déconnexion
        await logout();
        return false;
      }
    } catch (e) {
      await logout();
      return false;
    }
  }

  // Récupérer le profil de l'employé
  Future<void> fetchEmployeeProfile() async {
    try {
      final accessToken = await _storage.read(key: StorageKeys.accessToken);
      if (accessToken == null) {
        throw Exception('Token non disponible');
      }

      final response = await http.get(
        Uri.parse(ApiUrls.employeeProfile),
        headers: {
          'Authorization': 'Bearer $accessToken',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        _employeeProfile = Employee.fromJson(data);
        notifyListeners();
      } else if (response.statusCode == 401) {
        // Token expiré, tenter de le rafraîchir
        final refreshed = await refreshToken();
        if (refreshed) {
          // Réessayer après rafraîchissement
          await fetchEmployeeProfile();
        } else {
          _error = ErrorMessages.sessionExpired;
          notifyListeners();
        }
      } else if (response.statusCode == 404) {
        _error = ErrorMessages.noEmployeeProfile;
        notifyListeners();
      } else {
        _error = ErrorMessages.serverError;
        notifyListeners();
      }
    } catch (e) {
      _error = ErrorMessages.networkError;
      notifyListeners();
    }
  }

  // Obtenir un en-tête HTTP avec le token d'authentification
  Future<Map<String, String>> getAuthHeader() async {
    final accessToken = await _storage.read(key: StorageKeys.accessToken);
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    };
  }
}