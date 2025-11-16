// Clean Dashboard JavaScript - Mobile Scanner Integration

let currentScanData = null;
let scanPollingInterval = null;
let lastScanTimestamp = 0;

function startIssueProcess() {
    console.log('Issue process started');
    
    // Reset scan data to force new scan detection
    currentScanData = null;
    lastScanTimestamp = Date.now(); // Set to current time to ignore old scans
    
    try {
        const modalElement = document.getElementById('issueBookModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // Add event listener for when modal is fully shown
        modalElement.addEventListener('shown.bs.modal', function() {
            console.log('Issue modal fully shown - elements should be accessible');
            
            // Set scanner URL
            const scannerUrl = generateScannerUrl() + '?mode=issue';
            const scannerLink = document.getElementById('issue-scanner-link');
            if (scannerLink) {
                scannerLink.href = scannerUrl;
            }
            
            // Start polling after modal is fully shown
            startScanPolling('issue');
        }, { once: true }); // Use once: true to prevent multiple listeners
        
        modal.show();
    } catch (error) {
        console.error('Error opening modal:', error);
        showError('Error: ' + error.message);
    }
}

function generateScannerUrl() {
    const hostname = window.location.hostname;
    return `https://${hostname}:9000/scanner`;
}

function startScanPolling(mode) {
    if (scanPollingInterval) {
        clearInterval(scanPollingInterval);
    }
    scanPollingInterval = setInterval(() => checkForNewScan(mode), 2000);
}

async function checkForNewScan(mode) {
    try {
        const response = await fetch('/api/latest-scan');
        if (response.ok) {
            const scanData = await response.json();
            console.log('Polling result:', scanData);
            console.log('Last timestamp:', lastScanTimestamp);
            console.log('New timestamp:', scanData.timestamp);
            
            // Check if this is a new scan (timestamp is newer than last processed)
            if (scanData && scanData.timestamp > lastScanTimestamp) {
                console.log('New scan detected! Processing...');
                lastScanTimestamp = scanData.timestamp;
                processScanResult(scanData, mode);
            } else {
                console.log('No new scan data');
            }
        }
    } catch (error) {
        console.error('Error checking for scans:', error);
    }
}

function processScanResult(scanData, mode) {
    currentScanData = scanData;
    clearInterval(scanPollingInterval);
    
    if (mode === 'issue') {
        // Use a small delay to ensure modal elements are accessible
        setTimeout(() => {
            showIssueStep2(scanData);
        }, 100);
    } else if (mode === 'return') {
        setTimeout(() => {
            showReturnStep2(scanData);
        }, 100);
    }
}

function showIssueStep2(scanData) {
    // Try to find elements with retry logic
    let step1, step2, bookInfo;
    let attempts = 0;
    const maxAttempts = 10;
    
    const findElements = () => {
        step1 = document.getElementById('issue-step-1');
        step2 = document.getElementById('issue-step-2');
        bookInfo = document.getElementById('issue-book-info');
        
        // If bookInfo is still null, try alternative approaches
        if (!bookInfo && step2) {
            // Try to find it within step2
            bookInfo = step2.querySelector('#issue-book-info');
            if (!bookInfo) {
                // Try to find any element with that ID anywhere in the document
                bookInfo = document.querySelector('#issue-book-info');
            }
        }
        
        console.log(`Attempt ${attempts + 1}:`, { 
            step1: step1 ? 'found' : 'null', 
            step2: step2 ? 'found' : 'null', 
            bookInfo: bookInfo ? 'found' : 'null',
            step2Display: step2 ? step2.style.display : 'N/A',
            step2Visibility: step2 ? window.getComputedStyle(step2).display : 'N/A',
            allElementsWithId: document.querySelectorAll('[id*="issue-book-info"]').length
        });
        
        if (step1 && step2 && bookInfo) {
            return true;
        }
        return false;
    };
    
    const tryFindElements = () => {
        if (findElements()) {
            processElements();
        } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(tryFindElements, 100);
        } else {
            console.error('Modal elements not found after maximum attempts:', { step1, step2, bookInfo });
            
            // Fallback: try to create the element if step2 exists but bookInfo doesn't
            if (step1 && step2 && !bookInfo) {
                console.log('Attempting to create missing bookInfo element...');
                bookInfo = document.createElement('div');
                bookInfo.id = 'issue-book-info';
                bookInfo.className = 'alert alert-success';
                step2.appendChild(bookInfo);
                console.log('Created bookInfo element:', bookInfo);
                processElements();
            } else {
                showWarning(`Book scanned: ${scanData.book_info?.title}. Modal elements not found - please refresh and try again.`);
            }
        }
    };
    
    const processElements = () => {
        console.log('All elements found, processing...');
        step1.style.display = 'none';
        step2.style.display = 'block';
        
        if (scanData.found && scanData.book_info) {
            const book = scanData.book_info;
            bookInfo.className = 'alert alert-success';
            bookInfo.innerHTML = `<h6>📚 ${book.title}</h6><p><strong>Author:</strong> ${book.author}<br><strong>Barcode:</strong> ${book.barcode_id}<br><strong>Available:</strong> ${book.available_copies}</p>`;
            
            if (!book.is_available) {
                bookInfo.className = 'alert alert-danger';
                bookInfo.innerHTML += '<p class="text-danger"><strong>⚠️ Not available!</strong></p>';
            }
        } else {
            bookInfo.className = 'alert alert-danger';
            bookInfo.innerHTML = '<p><strong>❌ Book not found!</strong></p>';
        }
        
        // Load users for the dropdown
        loadUsers();
    };
    
    tryFindElements();
}

function showReturnStep2(scanData) {
    console.log('showReturnStep2 called with:', scanData);
    
    // Simplified approach - directly find elements
    const step1 = document.getElementById('return-step-1');
    const step2 = document.getElementById('return-step-2');
    const bookInfo = document.getElementById('return-book-info');
    
    if (!step1 || !step2 || !bookInfo) {
        console.error('Return modal elements not found:', { step1, step2, bookInfo });
        
        // Check if book was found and show appropriate message
        if (scanData.found && scanData.book_info) {
            const book = scanData.book_info;
            
            // Check if book is currently issued
            if (scanData.transaction_info) {
                const trans = scanData.transaction_info;
                showConfirm(
                    `<strong>Book:</strong> ${book.title}<br><strong>Issued to:</strong> ${trans.user_name}<br><strong>Due:</strong> ${new Date(trans.due_date).toLocaleDateString()}<br><br>Do you want to return this book?`,
                    () => {
                        // User confirmed - return the book
                        completeReturnDirect(scanData.book_info.barcode_id);
                    },
                    null,
                    'warning'
                );
            } else {
                showWarning(`Book "${book.title}" is not currently issued and cannot be returned.`);
            }
        } else {
            showError('Book not found. Please check the barcode and try again.');
        }
        return;
    }
    
    // Elements found - proceed normally
    step1.style.display = 'none';
    step2.style.display = 'block';
    
    if (scanData.found && scanData.book_info) {
        const book = scanData.book_info;
        
        if (scanData.transaction_info) {
            const trans = scanData.transaction_info;
            bookInfo.className = 'alert alert-success';
            bookInfo.innerHTML = `
                <h6>📚 ${book.title}</h6>
                <p><strong>Author:</strong> ${book.author}</p>
                <p><strong>Barcode:</strong> ${book.barcode_id}</p>
                <hr>
                <p><strong>Issued to:</strong> ${trans.user_name}<br>
                <strong>Due Date:</strong> ${new Date(trans.due_date).toLocaleDateString()}</p>
                <div class="alert alert-info mt-2">
                    <i class="bi bi-info-circle me-2"></i>Ready to return this book
                </div>
            `;
        } else {
            bookInfo.className = 'alert alert-danger';
            bookInfo.innerHTML = `
                <h6>📚 ${book.title}</h6>
                <p><strong>Barcode:</strong> ${book.barcode_id}</p>
                <hr>
                <p class="text-danger"><strong>⚠️ This book is not currently issued!</strong></p>
            `;
            // Disable the return button
            document.getElementById('return-complete-btn').disabled = true;
        }
    } else {
        bookInfo.className = 'alert alert-danger';
        bookInfo.innerHTML = '<p><strong>❌ Book not found!</strong></p>';
        document.getElementById('return-complete-btn').disabled = true;
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/users/json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const users = await response.json();
        
        const userSelect = document.getElementById('issue-user-select');
        if (!userSelect) {
            console.error('User select element not found');
            return;
        }
        
        userSelect.innerHTML = '<option value="">Select a user...</option>';
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.name} (${user.email})`;
            userSelect.appendChild(option);
        });
        
        userSelect.onchange = function() {
            const completeBtn = document.getElementById('issue-complete-btn');
            if (completeBtn) {
                completeBtn.disabled = !this.value;
            }
        };
        
        console.log(`Loaded ${users.length} users`);
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Error loading users: ' + error.message);
    }
}

function startReturnProcess() {
    console.log('Return process started');
    
    // Reset scan data to force new scan detection
    currentScanData = null;
    lastScanTimestamp = Date.now(); // Set to current time to ignore old scans
    
    try {
        const modalElement = document.getElementById('returnBookModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // Add event listener for when modal is fully shown
        modalElement.addEventListener('shown.bs.modal', function() {
            console.log('Return modal fully shown - elements should be accessible');
            
            // Set scanner URL
            const scannerUrl = generateScannerUrl() + '?mode=return';
            const scannerLink = document.getElementById('return-scanner-link');
            if (scannerLink) {
                scannerLink.href = scannerUrl;
            }
            
            // Start polling after modal is fully shown
            startScanPolling('return');
        }, { once: true }); // Use once: true to prevent multiple listeners
        
        modal.show();
    } catch (error) {
        console.error('Error opening modal:', error);
        showError('Error: ' + error.message);
    }
}

async function completeIssue() {
    const userId = document.getElementById('issue-user-select').value;
    if (!userId || !currentScanData) {
        showWarning('Please select a user and ensure book is scanned');
        return;
    }
    
    try {
        const response = await fetch('/api/scan/issue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: parseInt(userId),
                barcode_id: currentScanData.book_info.barcode_id
            })
        });
        
        const result = await response.json();
        if (result.success) {
            showSuccess('Book issued successfully!', 'Success');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('issueBookModal')).hide();
                location.reload();
            }, 1500);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError(error.message);
    }
}

async function completeReturn() {
    if (!currentScanData) {
        showWarning('Please scan a book first');
        return;
    }
    
    await completeReturnDirect(currentScanData.book_info.barcode_id);
}

async function completeReturnDirect(barcodeId) {
    try {
        const response = await fetch('/api/scan/return', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            body: JSON.stringify({ barcode_id: barcodeId })
        });
        
        const result = await response.json();
        if (result.success) {
            showSuccess('Book returned successfully!', 'Success');
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('returnBookModal'));
                if (modal) modal.hide();
                location.reload();
            }, 1500);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError(error.message);
    }
}

function resetIssueProcess() {
    document.getElementById('issue-step-1').style.display = 'block';
    document.getElementById('issue-step-2').style.display = 'none';
    currentScanData = null;
    lastScanTimestamp = Date.now(); // Set to current time to ignore old scans
    startScanPolling('issue');
}

function resetReturnProcess() {
    document.getElementById('return-step-1').style.display = 'block';
    document.getElementById('return-step-2').style.display = 'none';
    currentScanData = null;
    lastScanTimestamp = Date.now(); // Set to current time to ignore old scans
    startScanPolling('return');
}

// Test function
function testDashboard() {
    console.log('Dashboard functions loaded successfully');
    console.log('startIssueProcess available:', typeof startIssueProcess);
    console.log('startReturnProcess available:', typeof startReturnProcess);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JavaScript loaded');
    testDashboard();
});

console.log('Clean dashboard script loaded');