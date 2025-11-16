class ApiConfig {
  // Update this with your backend server URL
  // 
  // IMPORTANT: For Android devices, you cannot use 'localhost'
  // - For Android Emulator: use 'http://172.20.58.153:5000/api'
  // - For Physical Device: use 'http://YOUR_COMPUTER_IP:5000/api' 
  //   (e.g., 'http://192.168.1.100:5000/api')
  // - For localhost testing on web: use 'http://localhost:5000/api'
  //
  // To find your computer's IP address:
  // - Windows: ipconfig (look for IPv4 Address)
  // - Mac/Linux: ifconfig or ip addr
  //
  // Default: Using emulator address - change if using physical device
  static const String baseUrl = 'http://10.228.29.59:5001/api';
  
  // API Endpoints
  static const String login = '/auth/login';
  static const String userProfile = '/user/profile';
  static const String borrowedBooks = '/user/borrowed-books';
  static const String fines = '/user/fines';
  static const String notifications = '/user/notifications';
  static const String dashboardStats = '/user/dashboard-stats';
  static const String availableBooks = '/books/available';
  static const String searchBooks = '/books/search';
  
  // Headers
  static Map<String, String> getHeaders(String? token) {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
}

