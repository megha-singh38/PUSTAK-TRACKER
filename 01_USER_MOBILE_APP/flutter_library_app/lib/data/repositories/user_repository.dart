import '../../core/config/api_config.dart';
import '../services/api_service.dart';
import '../models/user.dart';
import '../models/borrowed_book.dart';
import '../models/fine.dart';
import '../models/notification.dart';

class UserRepository {
  final ApiService _apiService = ApiService();

  Future<User> getUserProfile() async {
    try {
      final response = await _apiService.get(ApiConfig.userProfile);
      return User.fromJson(response.data['user'] ?? response.data);
    } catch (e) {
      throw Exception('Failed to load user profile: $e');
    }
  }

  Future<List<BorrowedBook>> getBorrowedBooks() async {
    try {
      final response = await _apiService.get(ApiConfig.borrowedBooks);
      final List<dynamic> data = response.data['books'] ?? response.data;
      return data.map((json) => BorrowedBook.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load borrowed books: $e');
    }
  }

  Future<List<Fine>> getFines() async {
    try {
      final response = await _apiService.get(ApiConfig.fines);
      final List<dynamic> data = response.data['fines'] ?? response.data;
      return data.map((json) => Fine.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load fines: $e');
    }
  }

  Future<List<AppNotification>> getNotifications() async {
    try {
      final response = await _apiService.get(ApiConfig.notifications);
      final List<dynamic> data = response.data['notifications'] ?? response.data;
      return data.map((json) => AppNotification.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load notifications: $e');
    }
  }

  Future<bool> markNotificationAsRead(int notificationId) async {
    try {
      final response = await _apiService.put(
        '${ApiConfig.notifications}/$notificationId/read',
      );
      return response.data['success'] ?? true;
    } catch (e) {
      throw Exception('Failed to mark notification as read: $e');
    }
  }

  Future<Map<String, dynamic>> getDashboardStats() async {
    try {
      final response = await _apiService.get(ApiConfig.dashboardStats);
      return {
        'borrowed_count': response.data['borrowed_count'] ?? 0,
        'overdue_count': response.data['overdue_count'] ?? 0,
        'total_fines': (response.data['total_fines'] ?? 0).toDouble(),
      };
    } catch (e) {
      throw Exception('Failed to load dashboard stats: $e');
    }
  }
}

