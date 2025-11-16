import 'package:flutter/foundation.dart';
import '../data/models/user.dart';
import '../data/models/borrowed_book.dart';
import '../data/models/fine.dart';
import '../data/repositories/user_repository.dart';

class UserProvider with ChangeNotifier {
  final UserRepository _userRepository = UserRepository();

  User? _user;
  List<BorrowedBook> _borrowedBooks = [];
  List<Fine> _fines = [];
  bool _isLoading = false;
  String? _error;

  User? get user => _user;
  List<BorrowedBook> get borrowedBooks => _borrowedBooks;
  List<Fine> get fines => _fines;
  bool get isLoading => _isLoading;
  String? get error => _error;

  int _borrowedCount = 0;
  int _overdueCount = 0;
  double _totalFines = 0.0;

  int get borrowedCount => _borrowedCount > 0 ? _borrowedCount : _borrowedBooks.length;
  int get overdueCount => _overdueCount > 0 ? _overdueCount : _borrowedBooks.where((b) => b.status == 'overdue').length;
  double get totalFines => _totalFines > 0 ? _totalFines : _fines.where((f) => f.status == 'pending').fold(0.0, (sum, f) => sum + f.amount);

  Future<void> loadUserProfile() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _user = await _userRepository.getUserProfile();
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadBorrowedBooks() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _borrowedBooks = await _userRepository.getBorrowedBooks();
      // Update counts from loaded books
      _borrowedCount = _borrowedBooks.length;
      _overdueCount = _borrowedBooks.where((b) => b.status == 'overdue').length;
      _error = null;
    } catch (e) {
      _error = e.toString();
      _borrowedBooks = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadFines() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _fines = await _userRepository.getFines();
      // Update total fines from loaded fines
      _totalFines = _fines.where((f) => f.status == 'pending').fold(0.0, (sum, f) => sum + f.amount);
      _error = null;
    } catch (e) {
      _error = e.toString();
      _fines = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadDashboardStats() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final stats = await _userRepository.getDashboardStats();
      _borrowedCount = stats['borrowed_count'] ?? 0;
      _overdueCount = stats['overdue_count'] ?? 0;
      _totalFines = stats['total_fines'] ?? 0.0;
      _error = null;
    } catch (e) {
      _error = e.toString();
      // Fallback to calculating from borrowedBooks
      _borrowedCount = _borrowedBooks.length;
      _overdueCount = _borrowedBooks.where((b) => b.status == 'overdue').length;
      _totalFines = _fines.where((f) => f.status == 'pending').fold(0.0, (sum, f) => sum + f.amount);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

