import 'package:flutter/foundation.dart';
import '../data/models/notification.dart';
import '../data/repositories/user_repository.dart';
import '../data/services/due_date_notification_manager.dart';

class NotificationProvider with ChangeNotifier {
  final UserRepository _userRepository = UserRepository();
  final DueDateNotificationManager _dueDateManager = DueDateNotificationManager();

  List<AppNotification> _notifications = [];
  bool _isLoading = false;
  String? _error;

  List<AppNotification> get notifications => _notifications;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get unreadCount => _notifications.where((n) => !n.seen).length;

  Future<void> loadNotifications() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _notifications = await _userRepository.getNotifications();
      
      // Also check and schedule due date notifications
      await _dueDateManager.checkAndScheduleNotifications();
      
      _error = null;
    } catch (e) {
      _error = e.toString();
      _notifications = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> markAsRead(int notificationId) async {
    try {
      await _userRepository.markNotificationAsRead(notificationId);
      final index = _notifications.indexWhere((n) => n.id == notificationId);
      if (index != -1) {
        _notifications[index] = AppNotification(
          id: _notifications[index].id,
          title: _notifications[index].title,
          body: _notifications[index].body,
          type: _notifications[index].type,
          createdAt: _notifications[index].createdAt,
          seen: true,
        );
        notifyListeners();
      }
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> testNotification() async {
    await _dueDateManager.testNotification();
  }

  Future<void> refreshDueDateNotifications() async {
    await _dueDateManager.checkAndScheduleNotifications();
  }

  Future<void> removeNotification(int notificationId) async {
    try {
      await _userRepository.markNotificationAsRead(notificationId);
      _notifications.removeWhere((n) => n.id == notificationId);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> clearAllNotifications() async {
    try {
      for (final notification in _notifications) {
        if (!notification.seen) {
          await _userRepository.markNotificationAsRead(notification.id);
        }
      }
      _notifications.clear();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }
}

