import 'package:dio/dio.dart';
import '../services/storage_service.dart';
import '../../core/config/api_config.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  late Dio _dio;
  final StorageService _storageService = StorageService();

  void init() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: ApiConfig.getHeaders(null),
      ),
    );

    // Add interceptor for token
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storageService.getToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) {
          if (error.response?.statusCode == 401 || error.response?.statusCode == 422) {
            // Token expired or invalid - handle logout
            _storageService.deleteToken();
          }
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> post(String path, {dynamic data}) async {
    try {
      return await _dio.post(path, data: data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> put(String path, {dynamic data}) async {
    try {
      return await _dio.put(path, data: data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> delete(String path) async {
    try {
      return await _dio.delete(path);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Connection timeout. Please try again.';
    } else if (error.type == DioExceptionType.connectionError) {
      return 'No internet connection. Please check your network.';
    } else if (error.response != null) {
      final statusCode = error.response!.statusCode;
      final responseData = error.response?.data;
      String errorMessage = 'An error occurred';
      
      if (responseData is Map<String, dynamic>) {
        errorMessage = responseData['error'] ?? 
                      responseData['message'] ?? 
                      errorMessage;
      }
      
      if (statusCode == 401) {
        return 'Unauthorized. Please login again.';
      } else if (statusCode == 404) {
        return 'Resource not found.';
      } else if (statusCode == 422) {
        return errorMessage.isNotEmpty ? errorMessage : 'Invalid request. Please check your input.';
      } else if (statusCode == 500) {
        return 'Server error. Please try again later.';
      } else {
        return errorMessage;
      }
    } else {
      return 'An unexpected error occurred';
    }
  }
}

