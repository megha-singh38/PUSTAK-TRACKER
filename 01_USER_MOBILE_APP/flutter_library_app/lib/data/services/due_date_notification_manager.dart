import 'package:flutter/foundation.dart';
import '../models/borrowed_book.dart';
import '../repositories/user_repository.dart';
import 'notification_service.dart';
import 'storage_service.dart';

class DueDateNotificationManager {
  static final DueDateNotificationManager _instance = DueDateNotificationManager._internal();
  factory DueDateNotificationManager() => _instance;
  DueDateNotificationManager._internal();

  final NotificationService _notificationService = NotificationService();
  final UserRepository _userRepository = UserRepository();
  final StorageService _storageService = StorageService();

  static const String _lastCheckKey = 'last_notification_check';
  static const int _reminderDays = 4; // Remind 4 days before due date

  Future<void> init() async {
    await _notificationService.init();
  }

  Future<void> checkAndScheduleNotifications() async {
    try {
      // Check if we've already checked today
      final lastCheck = await _storageService.getString(_lastCheckKey);
      final today = DateTime.now();
      final todayString = '${today.year}-${today.month}-${today.day}';
      
      if (lastCheck == todayString) {
        if (kDebugMode) {
          print('Notifications already checked today');
        }
        return;
      }

      // Get user's borrowed books
      final borrowedBooks = await _userRepository.getBorrowedBooks();
      
      // Cancel existing notifications to avoid duplicates
      await _cancelExistingDueDateNotifications();
      
      // Schedule notifications for books due in 4 days
      for (final borrowedBook in borrowedBooks) {
        await _scheduleBookDueDateNotification(borrowedBook);
      }
      
      // Update last check date
      await _storageService.saveString(_lastCheckKey, todayString);
      
      if (kDebugMode) {
        print('Scheduled notifications for ${borrowedBooks.length} books');
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error checking notifications: $e');
      }
    }
  }

  Future<void> _scheduleBookDueDateNotification(BorrowedBook borrowedBook) async {
    final dueDate = borrowedBook.dueDate;
    final reminderDate = dueDate.subtract(Duration(days: _reminderDays));
    final now = DateTime.now();

    // Only schedule if reminder date is in the future
    if (reminderDate.isAfter(now)) {
      final notificationId = _generateNotificationId(borrowedBook.book.id);
      
      await _notificationService.scheduleNotification(
        id: notificationId,
        title: 'Book Due Soon!',
        body: '${borrowedBook.book.title} is due in $_reminderDays days (${_formatDate(dueDate)})',
        scheduledDate: reminderDate,
        payload: 'book_due:${borrowedBook.book.id}',
      );
      
      if (kDebugMode) {
        print('Scheduled notification for ${borrowedBook.book.title} at $reminderDate');
      }
    }
    
    // Also schedule daily reminders if book is overdue
    if (dueDate.isBefore(now)) {
      final overdueNotificationId = _generateOverdueNotificationId(borrowedBook.book.id);
      
      await _notificationService.showInstantNotification(
        id: overdueNotificationId,
        title: 'Overdue Book!',
        body: '${borrowedBook.book.title} was due on ${_formatDate(dueDate)}. Please return it soon.',
        payload: 'book_overdue:${borrowedBook.book.id}',
      );
    }
  }

  Future<void> _cancelExistingDueDateNotifications() async {
    final pendingNotifications = await _notificationService.getPendingNotifications();
    
    for (final notification in pendingNotifications) {
      if (notification.payload?.startsWith('book_due:') == true ||
          notification.payload?.startsWith('book_overdue:') == true) {
        await _notificationService.cancelNotification(notification.id);
      }
    }
  }

  Future<void> scheduleNotificationForBook(BorrowedBook borrowedBook) async {
    await _scheduleBookDueDateNotification(borrowedBook);
  }

  Future<void> cancelNotificationForBook(int bookId) async {
    final notificationId = _generateNotificationId(bookId);
    final overdueNotificationId = _generateOverdueNotificationId(bookId);
    
    await _notificationService.cancelNotification(notificationId);
    await _notificationService.cancelNotification(overdueNotificationId);
  }

  int _generateNotificationId(int bookId) {
    // Generate unique notification ID based on book ID
    return 1000 + bookId;
  }

  int _generateOverdueNotificationId(int bookId) {
    // Generate unique overdue notification ID based on book ID
    return 2000 + bookId;
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  Future<void> startDailyNotificationCheck() async {
    // This would ideally be called by a background service
    // For now, we'll call it when the app starts and when user navigates to certain screens
    await checkAndScheduleNotifications();
  }

  Future<void> testNotification() async {
    await _notificationService.showInstantNotification(
      id: 9999,
      title: 'Test Notification',
      body: 'This is a test notification from Pustak Tracker',
      payload: 'test',
    );
  }
}
