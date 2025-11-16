// Main JavaScript for Pustak Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Dashboard Data (placeholder - in real system this would come from Flask API)
const dashboardData = {
    circulation: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        issued: [120, 150, 180, 140, 210, 250, 230, 260, 290, 310],
        returned: [100, 130, 160, 120, 190, 220, 210, 240, 270, 280],
    },
    categories: {
        names: ['Computer Science', 'Fiction', 'Management', 'History', 'Biographies'],
        counts: [450, 380, 310, 220, 150]
    }
};

// Initialize Charts
function initializeCharts() {
    // Monthly Circulation Trend Chart
    const ctxCirculation = document.getElementById('circulationChart');
    if (ctxCirculation) {
        new Chart(ctxCirculation, {
            type: 'line',
            data: {
                labels: dashboardData.circulation.labels,
                datasets: [{
                    label: 'Books Issued',
                    data: dashboardData.circulation.issued,
                    borderColor: '#3498db', 
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Books Returned',
                    data: dashboardData.circulation.returned,
                    borderColor: '#2ecc71', 
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { drawBorder: false }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                }
            }
        });
    }

    // Top Categories Chart
    const ctxCategory = document.getElementById('categoryChart');
    if (ctxCategory) {
        new Chart(ctxCategory, {
            type: 'bar',
            data: {
                labels: dashboardData.categories.names,
                datasets: [{
                    label: 'Borrow Count',
                    data: dashboardData.categories.counts,
                    backgroundColor: [
                        '#3498db', // Blue
                        '#e74c3c', // Red
                        '#f1c40f', // Yellow
                        '#2ecc71', // Green
                        '#9b59b6'  // Purple
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { drawBorder: false }
                    },
                    y: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Quick scan processing function
async function processScan() {
    const input = document.getElementById('quick-scan-input');
    if (input && input.value.trim()) {
        const value = input.value.trim();
        
        // Show loading state
        const button = document.querySelector('button[onclick="processScan()"]');
        const originalText = button.textContent;
        button.textContent = 'Processing...';
        button.disabled = true;
        
        try {
            const response = await fetch('/quick-scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ value: value })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show success message with details
                let message = data.message;
                
                if (data.type === 'book_available') {
                    message += `\n\nBook: ${data.book_title}\nAvailable Copies: ${data.available_copies}\nAction: Ready for checkout`;
                } else if (data.type === 'book_unavailable') {
                    message += `\n\nBook: ${data.book_title}\nAvailable Copies: ${data.available_copies}\nAction: Not available`;
                } else if (data.type === 'user_transactions') {
                    message += `\n\nUser: ${data.user_name}\nActive Transactions: ${data.transactions.length}`;
                    if (data.transactions.length > 0) {
                        message += '\n\nBooks to return:';
                        data.transactions.forEach(trans => {
                            const overdueText = trans.days_overdue > 0 ? ` (${trans.days_overdue} days overdue)` : '';
                            message += `\n- ${trans.book_title}${overdueText}`;
                        });
                    }
                } else if (data.type === 'user_no_transactions') {
                    message += `\n\nUser: ${data.user_name}\nAction: Ready for checkout`;
                }
                
                showAlert(message, 'success');
            } else {
                showAlert(data.error, 'danger');
            }
        } catch (error) {
            console.error('Quick scan error:', error);
            showAlert('Error processing scan. Please try again.', 'danger');
        } finally {
            // Reset button state
            button.textContent = originalText;
            button.disabled = false;
            input.value = '';
        }
    } else {
        showAlert('Please enter a scan value', 'warning');
    }
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container-fluid');
    if (alertContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
        
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// API Functions
async function makeApiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showAlert('An error occurred while processing your request.', 'danger');
        throw error;
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
});