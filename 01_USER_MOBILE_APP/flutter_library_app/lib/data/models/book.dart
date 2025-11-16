class Book {
  final int id;
  final String title;
  final String author;
  final String category;
  final int availableCopies;
  final int totalCopies;
  final String? description;
  final String? coverUrl;

  Book({
    required this.id,
    required this.title,
    required this.author,
    required this.category,
    required this.availableCopies,
    required this.totalCopies,
    this.description,
    this.coverUrl,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      id: json['id'] as int,
      title: json['title'] as String,
      author: json['author'] as String,
      category: json['category'] as String,
      availableCopies: json['available_copies'] as int? ?? 0,
      totalCopies: json['total_copies'] as int? ?? 0,
      description: json['description'] as String?,
      coverUrl: json['cover_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'author': author,
      'category': category,
      'available_copies': availableCopies,
      'total_copies': totalCopies,
      'description': description,
      'cover_url': coverUrl,
    };
  }

  bool get isAvailable => availableCopies > 0;
}

