import 'package:flutter/material.dart';

// API URLs
class ApiUrls {
  // Base URL - Remplacer par l'URL réelle de votre serveur
  static const String baseUrl = 'https://api.buskoguard.com/api';
  // Endpoints
  static const String login = '$baseUrl/login_employee_app/';
  static const String logout = '$baseUrl/logout_employee_app/';
  static const String refreshToken = '$baseUrl/token/refresh/';
  static const String employeeProfile = '$baseUrl/employee/profile/';
}

// Clés pour le stockage sécurisé
class StorageKeys {
  static const String accessToken = 'access_token';
  static const String refreshToken = 'refresh_token';
  static const String userId = 'user_id';
  static const String username = 'username';
  static const String isStaff = 'is_staff';
  static const String hasEmployeeProfile = 'has_employee_profile';
}

// Couleurs de l'application
class AppColors {
  static const Color primary = Color(0xFF0056A6);     // Bleu principal
  static const Color secondary = Color(0xFF2F80ED);   // Bleu secondaire
  static const Color accent = Color(0xFFFFAB00);      // Orange accent
  static const Color background = Color(0xFFF5F7FA);  // Gris clair
  static const Color surface = Colors.white;          // Surface (cartes)
  static const Color text = Color(0xFF2E384D);        // Texte principal
  static const Color textLight = Color(0xFF8798AD);   // Texte secondaire
  static const Color success = Color(0xFF4CAF50);     // Vert succès
  static const Color error = Color(0xFFE53935);       // Rouge erreur
  static const Color divider = Color(0xFFE0E6ED);     // Gris diviseur
}

// Thème de l'application
class AppTheme {
  static ThemeData get theme => ThemeData(
    primaryColor: AppColors.primary,
    primaryColorLight: AppColors.secondary,
    colorScheme: ColorScheme.light(
      primary: AppColors.primary,
      secondary: AppColors.secondary,
      surface: AppColors.surface,
      error: AppColors.error,
    ),
    scaffoldBackgroundColor: AppColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.primary,
      elevation: 0,
      centerTitle: true,
      iconTheme: IconThemeData(color: Colors.white),
      titleTextStyle: TextStyle(
        color: Colors.white,
        fontSize: 18.0,
        fontWeight: FontWeight.w600,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8.0),
        ),
        padding: const EdgeInsets.symmetric(vertical: 16.0, horizontal: 24.0),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.primary,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.0),
        borderSide: const BorderSide(color: AppColors.divider),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.0),
        borderSide: const BorderSide(color: AppColors.divider),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.0),
        borderSide: const BorderSide(color: AppColors.primary, width: 2.0),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.0),
        borderSide: const BorderSide(color: AppColors.error, width: 2.0),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 16.0),
    ),
    fontFamily: 'Poppins',
  );
}

// Format de texte
class TextStyles {
  static const TextStyle headline = TextStyle(
    fontSize: 24.0,
    fontWeight: FontWeight.bold,
    color: AppColors.text,
  );
  
  static const TextStyle title = TextStyle(
    fontSize: 18.0,
    fontWeight: FontWeight.w600,
    color: AppColors.text,
  );
  
  static const TextStyle subtitle = TextStyle(
    fontSize: 16.0,
    fontWeight: FontWeight.w500,
    color: AppColors.text,
  );
  
  static const TextStyle body = TextStyle(
    fontSize: 14.0,
    color: AppColors.text,
  );
  
  static const TextStyle caption = TextStyle(
    fontSize: 12.0,
    color: AppColors.textLight,
  );
}

// Messages d'erreur
class ErrorMessages {
  static const String networkError = "Erreur de connexion au serveur. Veuillez vérifier votre connexion internet.";
  static const String authFailed = "Échec de l'authentification. Veuillez vérifier vos identifiants.";
  static const String sessionExpired = "Votre session a expiré. Veuillez vous reconnecter.";
  static const String serverError = "Une erreur serveur s'est produite. Veuillez réessayer plus tard.";
  static const String unknownError = "Une erreur inconnue s'est produite. Veuillez réessayer.";
  static const String noEmployeeProfile = "Profil employé non trouvé. Veuillez contacter votre administrateur.";
}