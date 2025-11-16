class AppConstants {
  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String rememberMeKey = 'remember_me';
  
  // Notification Types
  static const String notificationReminder = 'reminder';
  static const String notificationOverdue = 'overdue';
  
  // Book Status
  static const String bookStatusActive = 'active';
  static const String bookStatusOverdue = 'overdue';
  static const String bookStatusReturned = 'returned';
  
  // Fine Status
  static const String fineStatusPending = 'pending';
  static const String fineStatusPaid = 'paid';
  
  // Due Date Thresholds (days)
  static const int dueSoonThreshold = 3;
}

