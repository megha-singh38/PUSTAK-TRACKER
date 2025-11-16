import '../../core/config/api_config.dart';
import '../services/api_service.dart';
import '../models/book.dart';

class BookRepository {
  final ApiService _apiService = ApiService();

  Future<List<Book>> getAvailableBooks() async {
    try {
      final response = await _apiService.get(ApiConfig.availableBooks);
      final List<dynamic> data = response.data['books'] ?? response.data;
      return data.map((json) => Book.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load books: $e');
    }
  }

  Future<List<Book>> searchBooks(String query) async {
    try {
      final response = await _apiService.get(
        ApiConfig.searchBooks,
        queryParameters: {'query': query},
      );
      final List<dynamic> data = response.data['books'] ?? response.data;
      return data.map((json) => Book.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to search books: $e');
    }
  }
}

