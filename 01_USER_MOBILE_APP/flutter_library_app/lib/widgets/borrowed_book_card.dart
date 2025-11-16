import 'package:flutter/material.dart' hide DateUtils;
import '../data/models/borrowed_book.dart';
import '../core/utils/date_utils.dart';

class BorrowedBookCard extends StatelessWidget {
  final BorrowedBook borrowedBook;

  const BorrowedBookCard({
    super.key,
    required this.borrowedBook,
  });

  Color _getDueDateColor() {
    if (DateUtils.isOverdue(borrowedBook.dueDate)) {
      return Colors.red;
    } else if (DateUtils.isDueSoon(borrowedBook.dueDate)) {
      return Colors.orange;
    } else {
      return Colors.green;
    }
  }

  String _getDueDateText() {
    if (DateUtils.isOverdue(borrowedBook.dueDate)) {
      return 'Overdue';
    } else if (DateUtils.isDueSoon(borrowedBook.dueDate)) {
      return 'Due Soon';
    } else {
      return 'On Time';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        borrowedBook.book.title,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).brightness == Brightness.dark 
                              ? Colors.white 
                              : Colors.black,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        borrowedBook.book.author,
                        style: TextStyle(
                          fontSize: 14,
                          color: Theme.of(context).brightness == Brightness.dark 
                              ? Colors.grey[300] 
                              : Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: _getDueDateColor().withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: _getDueDateColor(), width: 1.5),
                  ),
                  child: Text(
                    _getDueDateText(),
                    style: TextStyle(
                      color: _getDueDateColor(),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Issue Date',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).brightness == Brightness.dark 
                            ? Colors.grey[400] 
                            : Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      DateUtils.formatDate(borrowedBook.issueDate),
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: Theme.of(context).brightness == Brightness.dark 
                            ? Colors.white 
                            : Colors.black,
                      ),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Due Date',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).brightness == Brightness.dark 
                            ? Colors.grey[400] 
                            : Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      DateUtils.formatDate(borrowedBook.dueDate),
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: _getDueDateColor(),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

