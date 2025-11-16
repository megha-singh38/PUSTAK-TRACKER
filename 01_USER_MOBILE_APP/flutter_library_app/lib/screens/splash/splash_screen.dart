import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAuthentication();
    });
  }

  Future<void> _checkAuthentication() async {
    // Wait a moment for providers to be ready
    await Future.delayed(const Duration(milliseconds: 500));
    
    if (!mounted) return;
    
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    
    // Wait for auth provider to finish loading if it's still loading
    if (authProvider.isLoading) {
      // Listen to auth provider changes
      authProvider.addListener(_onAuthChanged);
      return;
    }
    
    _navigateBasedOnAuth(authProvider);
  }

  void _onAuthChanged() {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    if (!authProvider.isLoading && mounted) {
      authProvider.removeListener(_onAuthChanged);
      _navigateBasedOnAuth(authProvider);
    }
  }

  void _navigateBasedOnAuth(AuthProvider authProvider) {
    if (!mounted) return;
    
    if (authProvider.isAuthenticated) {
      context.go('/dashboard');
    } else {
      context.go('/login');
    }
  }

  @override
  void dispose() {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    authProvider.removeListener(_onAuthChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset(
              'assets/images/pustak_logo.png',
              width: 80,
              height: 80,
            ),
            const SizedBox(height: 16),
            const Text(
              'Pustak Tracker',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Library Management System',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}

