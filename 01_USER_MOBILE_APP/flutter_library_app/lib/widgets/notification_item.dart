import 'package:flutter/material.dart' hide DateUtils;
import '../data/models/notification.dart';
import '../core/utils/date_utils.dart';

class NotificationItem extends StatefulWidget {
  final AppNotification notification;
  final VoidCallback? onTap;
  final VoidCallback? onDismiss;

  const NotificationItem({
    super.key,
    required this.notification,
    this.onTap,
    this.onDismiss,
  });

  @override
  State<NotificationItem> createState() => _NotificationItemState();
}

class _NotificationItemState extends State<NotificationItem>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _slideAnimation;
  late Animation<double> _fadeAnimation;
  bool _isPressed = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _slideAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutBack,
    ));
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeIn,
    ));
    
    // Start animation when widget is created
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  IconData _getIcon() {
    switch (widget.notification.type) {
      case 'reminder':
        return Icons.notifications;
      case 'overdue':
        return Icons.warning;
      default:
        return Icons.info;
    }
  }

  Color _getColor() {
    switch (widget.notification.type) {
      case 'reminder':
        return Colors.blue;
      case 'overdue':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(50 * (1 - _slideAnimation.value), 0),
          child: Opacity(
            opacity: _fadeAnimation.value,
            child: Dismissible(
              key: Key('notification_${widget.notification.id}'),
              direction: DismissDirection.endToStart,
              background: Container(
                alignment: Alignment.centerRight,
                padding: const EdgeInsets.only(right: 20),
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.delete,
                  color: Colors.white,
                  size: 28,
                ),
              ),
              onDismissed: (direction) {
                widget.onDismiss?.call();
              },
              child: GestureDetector(
                onTapDown: (_) => setState(() => _isPressed = true),
                onTapUp: (_) {
                  setState(() => _isPressed = false);
                  widget.onTap?.call();
                },
                onTapCancel: () => setState(() => _isPressed = false),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                transform: Matrix4.identity()..scale(_isPressed ? 0.98 : 1.0),
                child: Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  color: widget.notification.seen ? null : Colors.blue[50],
                  elevation: _isPressed ? 8 : 4,
                  shadowColor: _getColor().withOpacity(0.3),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      gradient: _isPressed
                          ? LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                _getColor().withOpacity(0.1),
                                Colors.transparent,
                              ],
                            )
                          : null,
                    ),
                    child: ListTile(
                      leading: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        child: CircleAvatar(
                          backgroundColor: _getColor().withOpacity(_isPressed ? 0.2 : 0.1),
                          child: AnimatedRotation(
                            turns: _isPressed ? 0.1 : 0.0,
                            duration: const Duration(milliseconds: 200),
                            child: Icon(_getIcon(), color: _getColor()),
                          ),
                        ),
                      ),
                      title: AnimatedDefaultTextStyle(
                        duration: const Duration(milliseconds: 200),
                        style: TextStyle(
                          fontWeight: widget.notification.seen ? FontWeight.normal : FontWeight.bold,
                          color: _isPressed ? _getColor() : null,
                        ),
                        child: Text(widget.notification.title),
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 4),
                          Text(widget.notification.body),
                          const SizedBox(height: 4),
                          Text(
                            DateUtils.getRelativeTime(widget.notification.createdAt),
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                      trailing: widget.notification.seen
                          ? null
                          : AnimatedContainer(
                              duration: const Duration(milliseconds: 300),
                              width: _isPressed ? 10 : 8,
                              height: _isPressed ? 10 : 8,
                              decoration: BoxDecoration(
                                color: _getColor(),
                                shape: BoxShape.circle,
                                boxShadow: _isPressed
                                    ? [
                                        BoxShadow(
                                          color: _getColor().withOpacity(0.5),
                                          blurRadius: 4,
                                          spreadRadius: 1,
                                        ),
                                      ]
                                    : null,
                              ),
                            ),
                    ),
                  ),
                ),
              ),
            ),
            ),
          ),
        );
      },
    );
  }
}

