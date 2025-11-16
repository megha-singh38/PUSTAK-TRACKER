class AppNotification {
  final int id;
  final String title;
  final String body;
  final String type; // 'reminder', 'overdue', 'reservation'
  final DateTime createdAt;
  final bool seen;

  AppNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    required this.createdAt,
    required this.seen,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as int,
      title: json['title'] as String,
      body: json['body'] as String,
      type: json['type'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      seen: json['seen'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'body': body,
      'type': type,
      'created_at': createdAt.toIso8601String(),
      'seen': seen,
    };
  }
}

