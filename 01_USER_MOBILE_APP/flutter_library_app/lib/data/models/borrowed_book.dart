import 'book.dart';

class BorrowedBook {
  final int id;
  final Book book;
  final DateTime issueDate;
  final DateTime dueDate;
  final String status; // 'active', 'overdue', 'returned'

  BorrowedBook({
    required this.id,
    required this.book,
    required this.issueDate,
    required this.dueDate,
    required this.status,
  });

  factory BorrowedBook.fromJson(Map<String, dynamic> json) {
    return BorrowedBook(
      id: json['id'] as int,
      book: Book.fromJson(json['book'] as Map<String, dynamic>),
      issueDate: DateTime.parse(json['issue_date'] as String),
      dueDate: DateTime.parse(json['due_date'] as String),
      status: json['status'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'book': book.toJson(),
      'issue_date': issueDate.toIso8601String(),
      'due_date': dueDate.toIso8601String(),
      'status': status,
    };
  }
}

