import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';
import '../../providers/notification_provider.dart';
import '../../widgets/notification_item.dart';
import '../../widgets/bottom_nav_bar.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final RefreshController _refreshController = RefreshController(initialRefresh: false);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<NotificationProvider>(context, listen: false).loadNotifications();
    });
  }

  @override
  void dispose() {
    _refreshController.dispose();
    super.dispose();
  }

  void _onRefresh() async {
    final notificationProvider =
        Provider.of<NotificationProvider>(context, listen: false);
    await notificationProvider.loadNotifications();
    _refreshController.refreshCompleted();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          Consumer<NotificationProvider>(
            builder: (context, notificationProvider, _) {
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(Icons.notifications_active),
                    onPressed: () async {
                      await notificationProvider.testNotification();
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Test notification sent!'),
                            duration: Duration(seconds: 2),
                          ),
                        );
                      }
                    },
                    tooltip: 'Test notification',
                  ),
                  if (notificationProvider.notifications.isNotEmpty)
                    IconButton(
                      icon: const Icon(Icons.clear_all),
                      onPressed: () async {
                        final shouldClear = await showDialog<bool>(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Clear All Notifications'),
                            content: const Text('Are you sure you want to clear all notifications?'),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.of(context).pop(false),
                                child: const Text('Cancel'),
                              ),
                              TextButton(
                                onPressed: () => Navigator.of(context).pop(true),
                                child: const Text('Clear All'),
                              ),
                            ],
                          ),
                        );
                        
                        if (shouldClear == true) {
                          await notificationProvider.clearAllNotifications();
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('All notifications cleared'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                          }
                        }
                      },
                      tooltip: 'Clear all',
                    ),
                ],
              );
            },
          ),
        ],
      ),
      body: Consumer<NotificationProvider>(
        builder: (context, notificationProvider, _) {
          if (notificationProvider.isLoading &&
              notificationProvider.notifications.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (notificationProvider.error != null &&
              notificationProvider.notifications.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.error_outline,
                      size: 64,
                      color: Colors.red[300],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Error Loading Notifications',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      notificationProvider.error!,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () {
                        notificationProvider.clearError();
                        notificationProvider.loadNotifications();
                      },
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          if (notificationProvider.notifications.isEmpty) {
            return SmartRefresher(
              controller: _refreshController,
              onRefresh: _onRefresh,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.notifications_none,
                        size: 64, color: Colors.grey),
                    const SizedBox(height: 16),
                    Text(
                      'No notifications',
                      style: TextStyle(
                        fontSize: 18,
                        color: Theme.of(context).brightness == Brightness.dark 
                            ? Colors.white 
                            : Colors.black,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'You\'re all caught up!',
                      style: TextStyle(
                        color: Theme.of(context).brightness == Brightness.dark 
                            ? Colors.grey[300] 
                            : Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          return SmartRefresher(
            controller: _refreshController,
            onRefresh: _onRefresh,
            child: ListView.builder(
              itemCount: notificationProvider.notifications.length,
              itemBuilder: (context, index) {
                final notification = notificationProvider.notifications[index];
                return NotificationItem(
                  notification: notification,
                  onTap: () {
                    if (!notification.seen) {
                      notificationProvider.markAsRead(notification.id);
                    }
                  },
                  onDismiss: () async {
                    await notificationProvider.removeNotification(notification.id);
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('${notification.title} dismissed'),
                          duration: const Duration(seconds: 2),
                          action: SnackBarAction(
                            label: 'Undo',
                            onPressed: () {
                              // Add back to notifications (would need to implement undo functionality)
                            },
                          ),
                        ),
                      );
                    }
                  },
                );
              },
            ),
          );
        },
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 3),
    );
  }
}

