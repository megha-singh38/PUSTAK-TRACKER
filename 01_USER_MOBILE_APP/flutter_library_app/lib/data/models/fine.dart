class Fine {
  final int id;
  final double amount;
  final String reason;
  final DateTime date;
  final String status; // 'pending', 'paid'

  Fine({
    required this.id,
    required this.amount,
    required this.reason,
    required this.date,
    required this.status,
  });

  factory Fine.fromJson(Map<String, dynamic> json) {
    return Fine(
      id: json['id'] as int,
      amount: (json['amount'] as num).toDouble(),
      reason: json['reason'] as String,
      date: DateTime.parse(json['date'] as String),
      status: json['status'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'amount': amount,
      'reason': reason,
      'date': date.toIso8601String(),
      'status': status,
    };
  }
}

