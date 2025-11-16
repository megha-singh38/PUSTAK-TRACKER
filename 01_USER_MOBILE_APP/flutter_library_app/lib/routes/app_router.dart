import 'package:go_router/go_router.dart';
import '../screens/splash/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/home/dashboard_screen.dart';
import '../screens/books/book_list_screen.dart';
import '../screens/books/book_detail_screen.dart';
import '../screens/library/my_books_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/profile/profile_screen.dart';

class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: '/books',
        builder: (context, state) => const BookListScreen(),
      ),
      GoRoute(
        path: '/books/:id',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return BookDetailScreen(bookId: id);
        },
      ),
      GoRoute(
        path: '/my-books',
        builder: (context, state) => const MyBooksScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
    ],
  );
}

