import 'package:flutter/foundation.dart';
import '../data/models/user.dart';
import '../data/repositories/auth_repository.dart';
import '../data/repositories/user_repository.dart';
import '../data/services/storage_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthRepository _authRepository = AuthRepository();
  final StorageService _storageService = StorageService();

  User? _user;
  bool _isLoading = false;
  bool _isAuthenticated = false;
  String? _error;

  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  Future<void> init() async {
    _isLoading = true;
    notifyListeners();

    try {
      final token = await _authRepository.getStoredToken();
      if (token != null && token.isNotEmpty) {
        _isAuthenticated = true;
        // Try to load user profile
        try {
          final userRepo = UserRepository();
          _user = await userRepo.getUserProfile();
        } catch (e) {
          // If profile load fails, user might need to login again
          _isAuthenticated = false;
          await _authRepository.logout();
        }
      }
    } catch (e) {
      _error = e.toString();
      _isAuthenticated = false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password, {bool rememberMe = false}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _authRepository.login(email, password, rememberMe: rememberMe);
      if (result['success'] == true) {
        _user = result['user'] as User;
        _isAuthenticated = true;
        await _storageService.saveString('user_data', _user!.email);
        
        // Save remember me preference
        await _storageService.saveBool('remember_me', rememberMe);
        if (rememberMe) {
          await _storageService.saveString('remembered_email', email);
        } else {
          await _storageService.remove('remembered_email');
        }
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = result['error'] as String? ?? 'Login failed';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authRepository.logout();
      _user = null;
      _isAuthenticated = false;
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<String?> getRememberedEmail() async {
    final rememberMe = await _storageService.getBool('remember_me') ?? false;
    if (rememberMe) {
      return await _storageService.getString('remembered_email');
    }
    return null;
  }

  Future<bool> getRememberMePreference() async {
    return await _storageService.getBool('remember_me') ?? false;
  }
}

