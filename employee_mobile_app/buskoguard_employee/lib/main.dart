import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'constants.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';
import 'screens/employee_profile_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Fixer l'orientation de l'app en mode portrait
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
      ],
      child: MaterialApp(
        title: 'BuskoGuard Mobile',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.theme,
        home: const AuthWrapper(),
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('fr', 'HT'), // Français d'Haïti
          Locale('fr', ''), // Français
          Locale('en', ''), // Anglais
          Locale('ht', ''), // Créole haïtien
        ],
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Écran de chargement initial
    return Consumer<AuthService>(
      builder: (context, authService, _) {
        // Afficher un écran de chargement pendant la vérification du statut d'authentification
        if (authService.isLoading) {
          return Scaffold(
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Icône placeholder au lieu d'un logo
                  Container(
                    height: 80,
                    width: 80,
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Center(
                      child: Text(
                        'BG',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'BuskoGuard Mobile',
                    style: TextStyles.title,
                  ),
                  const SizedBox(height: 32),
                  const CircularProgressIndicator(),
                ],
              ),
            ),
          );
        }
        
        // Rediriger vers l'écran approprié en fonction du statut d'authentification
        if (authService.isAuthenticated) {
          return const EmployeeProfileScreen();
        } else {
          return const LoginScreen();
        }
      },
    );
  }
}