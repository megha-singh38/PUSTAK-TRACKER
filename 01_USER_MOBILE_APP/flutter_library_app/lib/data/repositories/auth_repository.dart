import '../../core/config/api_config.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/user.dart';

class AuthRepository {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  Future<Map<String, dynamic>> login(String email, String password, {bool rememberMe = false}) async {
    try {
      final response = await _apiService.post(
        ApiConfig.login,
        data: {
          'email': email,
          'password': password,
        },
      );

      final token = response.data['token'] as String;
      final userData = response.data['user'] as Map<String, dynamic>;
      final user = User.fromJson(userData);

      // Store token
      await _storageService.saveToken(token);

      return {
        'success': true,
        'user': user,
        'token': token,
      };
    } catch (e) {
      return {
        'success': false,
        'error': e.toString(),
      };
    }
  }

  Future<void> logout() async {
    await _storageService.deleteToken();
    await _storageService.remove('user_data');
  }

  Future<String?> getStoredToken() async {
    return await _storageService.getToken();
  }

  Future<bool> isLoggedIn() async {
    final token = await _storageService.getToken();
    return token != null && token.isNotEmpty;
  }
}

