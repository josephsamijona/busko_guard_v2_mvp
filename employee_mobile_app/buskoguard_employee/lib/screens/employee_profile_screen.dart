import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:image_gallery_saver/image_gallery_saver.dart';
import 'package:permission_handler/permission_handler.dart';
import '../constants.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';

class EmployeeProfileScreen extends StatefulWidget {
  const EmployeeProfileScreen({super.key});

  @override
  State<EmployeeProfileScreen> createState() => _EmployeeProfileScreenState();
}

class _EmployeeProfileScreenState extends State<EmployeeProfileScreen> {
  @override
  void initState() {
    super.initState();
    // Charger le profil au chargement de l'écran si nécessaire
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authService = Provider.of<AuthService>(context, listen: false);
      if (authService.employeeProfile == null) {
        authService.fetchEmployeeProfile();
      }
    });
  }

  // Sauvegarder le QR code dans la galerie
  Future<void> _saveQrCodeToGallery(BuildContext context) async {
    final authService = Provider.of<AuthService>(context, listen: false);
    final employee = authService.employeeProfile;
    
    if (employee?.qrCodeImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Aucun QR code disponible à enregistrer."))
      );
      return;
    }

    try {
      // Vérifier et demander la permission
      var status = await Permission.storage.status;
      if (!status.isGranted) {
        status = await Permission.storage.request();
        if (!status.isGranted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Permission de stockage requise pour enregistrer le QR code."))
          );
          return;
        }
      }

      // Extraire les données d'image à partir du base64
      final dataUri = employee!.qrCodeImage!;
      final dataPart = dataUri.split(',')[1];
      final bytes = base64Decode(dataPart);

      // Enregistrer l'image
      final result = await ImageGallerySaver.saveImage(
        Uint8List.fromList(bytes),
        quality: 100,
        name: "qrcode_${employee.employeeId}"
      );

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("QR code enregistré dans la galerie"))
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Erreur lors de l'enregistrement: $e"))
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    final employee = authService.employeeProfile;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Profil Employé"),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await authService.logout();
              if (mounted) {
                Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: authService.isLoading
          ? const Center(child: CircularProgressIndicator())
          : authService.error != null && employee == null
              ? _buildErrorView(authService.error!)
              : _buildProfileView(employee),
    );
  }

  Widget _buildErrorView(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              color: AppColors.error,
              size: 60,
            ),
            const SizedBox(height: 16),
            Text(
              "Erreur",
              style: TextStyles.headline.copyWith(color: AppColors.error),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: TextStyles.body,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text("Réessayer"),
              onPressed: () {
                final authService = Provider.of<AuthService>(context, listen: false);
                authService.fetchEmployeeProfile();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileView(employee) {
    if (employee == null) {
      return const Center(child: Text("Aucune donnée employé disponible"));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Carte d'identité employé
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  // En-tête de la carte
                  Row(
                    children: [
                      Container(
                        height: 40,
                        width: 40,
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Center(
                          child: Text(
                            'BG',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'CARTE D\'IDENTITÉ EMPLOYÉ',
                          style: TextStyles.title,
                        ),
                      ),
                    ],
                  ),
                  const Divider(height: 24, color: AppColors.divider),
                  
                  // Informations employé
                  _buildInfoRow("Nom complet", employee.fullName),
                  _buildInfoRow("ID Employé", employee.employeeId),
                  _buildInfoRow(
                    "Département", 
                    employee.department?.name ?? "Non assigné"
                  ),
                  _buildInfoRow(
                    "Rôle", 
                    employee.role?.name ?? "Non assigné"
                  ),
                  _buildInfoRow("Email", employee.user.email),
                  if (employee.user.phoneNumber != null)
                    _buildInfoRow("Téléphone", employee.user.phoneNumber!),
                  
                  const SizedBox(height: 16),
                  
                  // QR Code
                  if (employee.qrCodeImage != null) ...[
                    const Divider(height: 24, color: AppColors.divider),
                    const Text(
                      "QR Code d'identification",
                      style: TextStyles.subtitle,
                    ),
                    const SizedBox(height: 16),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.divider),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      padding: const EdgeInsets.all(16),
                      child: Image.memory(
                        base64Decode(employee.qrCodeImage!.split(',')[1]),
                        height: 200,
                        width: 200,
                        fit: BoxFit.contain,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        OutlinedButton.icon(
                          icon: const Icon(Icons.download),
                          label: const Text("Sauvegarder"),
                          onPressed: () => _saveQrCodeToGallery(context),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Informations supplémentaires
          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Utilisation du QR Code",
                    style: TextStyles.subtitle,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    "Présentez ce QR code au scanner de l'entreprise pour enregistrer vos heures de travail ou accéder aux locaux.",
                    style: TextStyles.body,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyles.caption.copyWith(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyles.body,
            ),
          ),
        ],
      ),
    );
  }
}