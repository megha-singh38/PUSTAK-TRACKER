import 'package:flutter/material.dart';
import 'package:flutter_library_app/routes/app_router.dart';
import 'package:flutter_library_app/core/theme/app_theme.dart';

// --- Main App Widget ---
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Pustak Tracker',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: AppRouter.router,
    );
  }
}