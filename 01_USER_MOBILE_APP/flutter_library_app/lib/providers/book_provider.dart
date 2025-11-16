import 'package:flutter/foundation.dart';
import '../data/models/book.dart';
import '../data/repositories/book_repository.dart';

class BookProvider with ChangeNotifier {
  final BookRepository _bookRepository = BookRepository();

  List<Book> _books = [];
  List<Book> _filteredBooks = [];
  bool _isLoading = false;
  String? _error;
  String _searchQuery = '';

  List<Book> get books => _filteredBooks.isEmpty && _searchQuery.isEmpty ? _books : _filteredBooks;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadBooks() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _books = await _bookRepository.getAvailableBooks();
      _filteredBooks = _books;
      _error = null;
    } catch (e) {
      _error = e.toString();
      _books = [];
      _filteredBooks = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> searchBooks(String query) async {
    _searchQuery = query;
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      if (query.isEmpty) {
        _filteredBooks = _books;
      } else {
        _filteredBooks = await _bookRepository.searchBooks(query);
      }
      _error = null;
    } catch (e) {
      _error = e.toString();
      _filteredBooks = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void filterByCategory(String? category) {
    if (category == null || category.isEmpty) {
      _filteredBooks = _books;
    } else {
      _filteredBooks = _books.where((book) => book.category == category).toList();
    }
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

