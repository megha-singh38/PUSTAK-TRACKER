import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_native_splash/flutter_native_splash.dart';
import 'package:flutter_library_app/app.dart';
import 'package:flutter_library_app/providers/auth_provider.dart';
import 'package:flutter_library_app/providers/book_provider.dart';
import 'package:flutter_library_app/providers/user_provider.dart';
import 'package:flutter_library_app/providers/notification_provider.dart';
import 'package:flutter_library_app/data/services/api_service.dart';
import 'package:flutter_library_app/data/services/storage_service.dart';
import 'package:flutter_library_app/data/services/due_date_notification_manager.dart';

void main() async {
  // Ensure that Flutter bindings are initialized before calling native code
  WidgetsBinding widgetsBinding = WidgetsFlutterBinding.ensureInitialized();
  
  // Preserve the splash screen during initialization
  FlutterNativeSplash.preserve(widgetsBinding: widgetsBinding);

  // Initialize storage service
  await StorageService().init();

  // Initialize API service
  ApiService().init();

  // Initialize notification manager
  await DueDateNotificationManager().init();

  // Create providers
  final authProvider = AuthProvider();
  await authProvider.init();

  // Remove the splash screen after initialization is complete
  FlutterNativeSplash.remove();

  // Run the app with providers
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: authProvider),
        ChangeNotifierProvider(create: (_) => BookProvider()),
        ChangeNotifierProvider(create: (_) => UserProvider()),
        ChangeNotifierProvider(create: (_) => NotificationProvider()),
      ],
      child: const App(),
    ),
  );
}