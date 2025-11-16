class BarcodeScanner {
    constructor() {
        this.codeReader = null;
        this.video = document.getElementById('video');
        this.statusElement = document.getElementById('status');
        this.statusText = document.getElementById('status-text');
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.scanAgainBtn = document.getElementById('scan-again-btn');
        this.bookInfoDiv = document.getElementById('book-info');
        this.errorInfoDiv = document.getElementById('error-info');
        this.manualInputCard = document.getElementById('manual-input-card');
        this.manualIsbnInput = document.getElementById('manual-isbn');
        this.lookupIsbnBtn = document.getElementById('lookup-isbn-btn');
        this.testCameraBtn = document.getElementById('test-camera-btn');
        this.browserWarning = document.getElementById('browser-warning');
        
        this.isScanning = false;
        this.lastScannedCode = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Initialize ZXing code reader
            this.codeReader = new ZXing.BrowserMultiFormatReader();
            
            // Set up event listeners
            this.startBtn.addEventListener('click', () => this.startScanning());
            this.stopBtn.addEventListener('click', () => this.stopScanning());
            this.scanAgainBtn.addEventListener('click', () => this.resetScanner());
            this.lookupIsbnBtn.addEventListener('click', () => this.lookupManualIsbn());
            this.manualIsbnInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.lookupManualIsbn();
                }
            });
            this.testCameraBtn.addEventListener('click', () => this.testCamera());
            
            // Check camera access support with fallbacks
            const hasCameraSupport = this.checkCameraSupport();
            if (hasCameraSupport) {
                this.updateStatus('Camera ready. Click "Start Scanning" to begin.', 'info');
                this.startBtn.disabled = false;
            } else {
                this.updateStatus('Camera not available. Use manual ISBN entry below.', 'warning');
                this.startBtn.disabled = true;
                this.showBrowserWarning();
            }
            
            // Always show manual input as fallback
            this.manualInputCard.style.display = 'block';
            
        } catch (error) {
            console.error('Error initializing scanner:', error);
            this.updateStatus('Scanner initialized. Use manual ISBN entry below.', 'info');
            this.startBtn.disabled = true;
            this.manualInputCard.style.display = 'block';
        }
    }
    
    checkCameraSupport() {
        console.log('=== CAMERA SUPPORT CHECK ===');
        console.log('navigator.mediaDevices:', navigator.mediaDevices);
        console.log('navigator.getUserMedia:', navigator.getUserMedia);
        console.log('navigator.webkitGetUserMedia:', navigator.webkitGetUserMedia);
        console.log('navigator.mozGetUserMedia:', navigator.mozGetUserMedia);
        console.log('navigator.msGetUserMedia:', navigator.msGetUserMedia);
        console.log('location.protocol:', location.protocol);
        console.log('location.hostname:', location.hostname);
        console.log('User Agent:', navigator.userAgent);
        
        // Check if we're on HTTPS or localhost
        const isSecure = location.protocol === 'https:' || 
                        location.hostname === 'localhost' || 
                        location.hostname === '127.0.0.1' ||
                        location.hostname.includes('192.168.') ||
                        location.hostname.includes('10.') ||
                        location.hostname.includes('172.');
        
        console.log('Is secure context:', isSecure);
        
        // Check for any camera API support
        const hasModernAPI = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
        const hasLegacyAPI = navigator.getUserMedia || 
                           navigator.webkitGetUserMedia || 
                           navigator.mozGetUserMedia || 
                           navigator.msGetUserMedia;
        
        const hasCameraSupport = hasModernAPI || hasLegacyAPI;
        
        console.log('Modern API available:', hasModernAPI);
        console.log('Legacy API available:', hasLegacyAPI);
        console.log('Camera support:', hasCameraSupport);
        
        return hasCameraSupport;
    }
    
    showBrowserWarning() {
        if (this.browserWarning) {
            this.browserWarning.style.display = 'block';
        }
    }
    
    async startScanning() {
        try {
            this.updateStatus('Starting camera...', 'warning');
            this.startBtn.disabled = true;
            
            console.log('=== STARTING CAMERA SCANNING ===');
            
            // Try to get camera stream with multiple fallback options
            let stream;
            let cameraConstraints = [
                // Option 1: Back camera with high quality
                { 
                    video: { 
                        facingMode: 'environment',
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                },
                // Option 2: Any camera with high quality
                { 
                    video: { 
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                },
                // Option 3: Basic camera access
                { video: true }
            ];
            
            for (let i = 0; i < cameraConstraints.length; i++) {
                try {
                    console.log(`Trying camera constraint ${i + 1}:`, cameraConstraints[i]);
                    
                    // Try modern API first
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        stream = await navigator.mediaDevices.getUserMedia(cameraConstraints[i]);
                        console.log('✅ Camera stream obtained with modern API');
                        break;
                    }
                    
                    // Try legacy APIs
                    const legacyAPIs = [
                        navigator.getUserMedia,
                        navigator.webkitGetUserMedia,
                        navigator.mozGetUserMedia,
                        navigator.msGetUserMedia
                    ];
                    
                    for (const getUserMedia of legacyAPIs) {
                        if (getUserMedia) {
                            try {
                                stream = await new Promise((resolve, reject) => {
                                    getUserMedia.call(navigator, cameraConstraints[i], resolve, reject);
                                });
                                console.log('✅ Camera stream obtained with legacy API');
                                break;
                            } catch (e) {
                                console.log('Legacy API failed:', e.message);
                            }
                        }
                    }
                    
                    if (stream) break;
                    
                } catch (error) {
                    console.log(`❌ Camera constraint ${i + 1} failed:`, error.message);
                    if (i === cameraConstraints.length - 1) {
                        throw error;
                    }
                }
            }
            
            if (!stream) {
                throw new Error('Could not access camera with any configuration');
            }
            
            // Stop the test stream
            stream.getTracks().forEach(track => track.stop());
            console.log('✅ Camera test successful');
            
            // Get available video devices
            let videoInputDevices = [];
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                videoInputDevices = devices.filter(device => device.kind === 'videoinput');
                console.log('📷 Available cameras:', videoInputDevices.length);
            } catch (deviceError) {
                console.warn('Could not enumerate devices:', deviceError);
            }
            
            // Use the first available camera or undefined for default
            const selectedDeviceId = videoInputDevices.length > 0 ? videoInputDevices[0].deviceId : undefined;
            console.log('🎯 Using camera device:', selectedDeviceId || 'default');
            
            // Start decoding from video stream
            await this.codeReader.decodeFromVideoDevice(
                selectedDeviceId,
                this.video,
                (result, err) => {
                    if (result) {
                        console.log('📱 Barcode detected:', result.getText());
                        this.handleScanResult(result);
                    }
                    if (err && !(err instanceof ZXing.NotFoundException)) {
                        console.log('Scan error:', err);
                    }
                }
            );
            
            this.isScanning = true;
            this.updateStatus('🎥 Camera active! Point camera at ISBN barcode.', 'success');
            this.stopBtn.disabled = false;
            console.log('✅ Camera scanning started successfully');
            
        } catch (error) {
            console.error('❌ Error starting scanner:', error);
            
            let errorMessage = 'Camera access failed: ';
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Permission denied. Please allow camera access and refresh the page.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No camera found. Please connect a camera device.';
            } else if (error.name === 'NotReadableError') {
                errorMessage += 'Camera is already in use by another application.';
            } else {
                errorMessage += error.message;
            }
            
            this.updateStatus(errorMessage, 'danger');
            this.startBtn.disabled = false;
        }
    }
    
    async stopScanning() {
        try {
            if (this.codeReader) {
                this.codeReader.reset();
            }
            
            this.isScanning = false;
            this.updateStatus('Scanning stopped.', 'info');
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            
        } catch (error) {
            console.error('Error stopping scanner:', error);
            this.updateStatus('Error stopping scanner: ' + error.message, 'danger');
        }
    }
    
    async handleScanResult(result) {
        const barcode = result.getText();
        
        // Prevent duplicate scans of the same barcode
        if (this.lastScannedCode === barcode) {
            return;
        }
        
        this.lastScannedCode = barcode;
        this.updateStatus(`Barcode detected: ${barcode}`, 'success');
        
        // Stop scanning temporarily
        this.stopScanning();
        
        // Show loading state
        this.updateStatus(`<div class="loading-spinner me-2"></div>Looking up book information...`, 'info');
        
        try {
            // Look up the book in the database
            const response = await fetch(`/api/barcode/${encodeURIComponent(barcode)}`);
            const data = await response.json();
            
            if (data.found) {
                this.displayBookInfo(data.book);
                this.updateStatus('Book found successfully!', 'success');
            } else {
                this.displayError(data.message || 'Book not found in database');
                this.updateStatus('Book not found in database', 'warning');
            }
            
        } catch (error) {
            console.error('Error looking up book:', error);
            this.displayError('Error looking up book: ' + error.message);
            this.updateStatus('Error looking up book', 'danger');
        }
        
        // Show scan again button
        this.scanAgainBtn.style.display = 'inline-block';
    }
    
    displayBookInfo(book) {
        // Hide error info if visible
        this.errorInfoDiv.style.display = 'none';
        
        // Create book info HTML
        const bookInfoHTML = `
            <div class="book-info">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="mb-2">
                            <i class="bi bi-book me-2"></i>
                            ${this.escapeHtml(book.title)}
                        </h5>
                        <p class="mb-1">
                            <strong>Author:</strong> ${this.escapeHtml(book.author)}
                        </p>
                        <p class="mb-1">
                            <strong>Publisher:</strong> ${this.escapeHtml(book.publisher || 'N/A')}
                        </p>
                        <p class="mb-1">
                            <strong>ISBN:</strong> ${this.escapeHtml(book.isbn)}
                        </p>
                        <p class="mb-1">
                            <strong>Category:</strong> ${this.escapeHtml(book.category_name || 'N/A')}
                        </p>
                        <p class="mb-0">
                            <strong>Copies:</strong> ${book.available_copies} available of ${book.total_copies} total
                        </p>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="mb-3">
                            <span class="status-badge badge bg-${book.is_available ? 'success' : 'danger'}">
                                <i class="bi bi-${book.is_available ? 'check-circle' : 'x-circle'} me-1"></i>
                                ${book.status}
                            </span>
                        </div>
                        <div class="small opacity-75">
                            Book ID: ${book.id}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.bookInfoDiv.innerHTML = bookInfoHTML;
        this.bookInfoDiv.style.display = 'block';
    }
    
    displayError(message) {
        // Hide book info if visible
        this.bookInfoDiv.style.display = 'none';
        
        // Create error info HTML
        const errorHTML = `
            <div class="error-message">
                <div class="text-center">
                    <i class="bi bi-exclamation-triangle fs-1 mb-3"></i>
                    <h5 class="mb-2">Book Not Found</h5>
                    <p class="mb-0">${this.escapeHtml(message)}</p>
                </div>
            </div>
        `;
        
        this.errorInfoDiv.innerHTML = errorHTML;
        this.errorInfoDiv.style.display = 'block';
    }
    
    resetScanner() {
        // Clear previous results
        this.bookInfoDiv.style.display = 'none';
        this.errorInfoDiv.style.display = 'none';
        this.scanAgainBtn.style.display = 'none';
        this.lastScannedCode = null;
        
        // Reset status
        this.updateStatus('Ready to scan. Click "Start Scanning" to begin.', 'info');
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
    }
    
    updateStatus(message, type) {
        this.statusText.innerHTML = message;
        this.statusElement.className = `alert alert-${type}`;
    }
    
    async testCamera() {
        this.testCameraBtn.disabled = true;
        this.updateStatus('Testing camera access...', 'warning');
        
        try {
            console.log('=== TESTING CAMERA ACCESS ===');
            console.log('navigator.mediaDevices:', navigator.mediaDevices);
            console.log('navigator.getUserMedia:', navigator.getUserMedia);
            console.log('navigator.webkitGetUserMedia:', navigator.webkitGetUserMedia);
            console.log('navigator.mozGetUserMedia:', navigator.mozGetUserMedia);
            console.log('navigator.msGetUserMedia:', navigator.msGetUserMedia);
            
            // Check if we're in Chrome
            const isChrome = navigator.userAgent.includes('Chrome') && !navigator.userAgent.includes('Edge');
            console.log('Is Chrome:', isChrome);
            
            if (isChrome) {
                console.log('=== CHROME-SPECIFIC TEST ===');
                console.log('Chrome version:', navigator.userAgent.match(/Chrome\/(\d+)/)?.[1]);
                console.log('Location protocol:', location.protocol);
                console.log('Location hostname:', location.hostname);
                console.log('Is secure context:', location.protocol === 'https:' || location.hostname === 'localhost');
            }
            
            // Try multiple approaches to get camera access
            let stream;
            let method = '';
            
            // Method 1: Modern MediaDevices API with Chrome-specific handling
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                try {
                    console.log('Trying modern MediaDevices API...');
                    
                    // Chrome-specific constraints
                    const constraints = isChrome ? {
                        video: {
                            width: { ideal: 1280 },
                            height: { ideal: 720 },
                            facingMode: 'environment'
                        }
                    } : { video: true };
                    
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    method = 'Modern MediaDevices API';
                    console.log('✅ Camera test successful with modern API');
                } catch (e) {
                    console.log('❌ Modern API failed:', e.name, e.message);
                    
                    // Try with basic constraints
                    try {
                        console.log('Trying with basic constraints...');
                        stream = await navigator.mediaDevices.getUserMedia({ video: true });
                        method = 'Modern MediaDevices API (basic)';
                        console.log('✅ Camera test successful with basic constraints');
                    } catch (e2) {
                        console.log('❌ Basic constraints also failed:', e2.name, e2.message);
                    }
                }
            }
            
            // Method 2: Legacy getUserMedia APIs
            if (!stream) {
                console.log('Trying legacy APIs...');
                const legacyAPIs = [
                    { name: 'getUserMedia', fn: navigator.getUserMedia },
                    { name: 'webkitGetUserMedia', fn: navigator.webkitGetUserMedia },
                    { name: 'mozGetUserMedia', fn: navigator.mozGetUserMedia },
                    { name: 'msGetUserMedia', fn: navigator.msGetUserMedia }
                ];
                
                for (const api of legacyAPIs) {
                    if (api.fn) {
                        try {
                            console.log(`Trying ${api.name}...`);
                            stream = await new Promise((resolve, reject) => {
                                api.fn.call(navigator, { video: true }, resolve, reject);
                            });
                            method = `Legacy ${api.name}`;
                            console.log(`✅ Camera test successful with ${api.name}`);
                            break;
                        } catch (e) {
                            console.log(`❌ ${api.name} failed:`, e.name, e.message);
                        }
                    }
                }
            }
            
            if (!stream) {
                throw new Error('No camera API available in this browser');
            }
            
            // Display video stream
            this.video.srcObject = stream;
            await this.video.play();
            
            this.updateStatus(`✅ Camera test successful! Using ${method}. Camera is working.`, 'success');
            this.startBtn.disabled = false;
            
            // Stop the test stream after 3 seconds
            setTimeout(() => {
                stream.getTracks().forEach(track => track.stop());
                this.video.srcObject = null;
                this.updateStatus('Camera test completed. Ready to scan!', 'info');
            }, 3000);
            
        } catch (error) {
            console.error('❌ Camera test failed:', error);
            
            let errorMessage = 'Camera test failed: ';
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Permission denied. Please allow camera access and refresh the page.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No camera found. Please connect a camera device.';
            } else if (error.name === 'NotReadableError') {
                errorMessage += 'Camera is in use by another app. Close other camera apps and try again.';
            } else if (error.message.includes('No camera API') || error.message.includes('getUserMedia is not supported')) {
                errorMessage += 'This browser does not support camera access. Please use Chrome, Firefox, or Safari.';
                this.showBrowserWarning();
            } else {
                errorMessage += error.message;
            }
            
            this.updateStatus(errorMessage, 'danger');
        }
        
        this.testCameraBtn.disabled = false;
    }
    
    async lookupManualIsbn() {
        const isbn = this.manualIsbnInput.value.trim();
        
        if (!isbn) {
            this.updateStatus('Please enter an ISBN', 'warning');
            return;
        }
        
        // Validate ISBN format (basic check)
        const cleanIsbn = isbn.replace(/[-\s]/g, '');
        if (!/^\d{10,13}$/.test(cleanIsbn)) {
            this.updateStatus('Please enter a valid ISBN (10-13 digits)', 'warning');
            return;
        }
        
        this.updateStatus(`<div class="loading-spinner me-2"></div>Looking up ISBN: ${cleanIsbn}...`, 'info');
        this.lookupIsbnBtn.disabled = true;
        
        try {
            // Look up the book in the database
            const response = await fetch(`/api/barcode/${encodeURIComponent(cleanIsbn)}`);
            const data = await response.json();
            
            if (data.found) {
                this.displayBookInfo(data.book);
                this.updateStatus('Book found successfully!', 'success');
            } else {
                this.displayError(data.message || 'Book not found in database');
                this.updateStatus('Book not found in database', 'warning');
            }
            
        } catch (error) {
            console.error('Error looking up ISBN:', error);
            this.displayError('Error looking up ISBN: ' + error.message);
            this.updateStatus('Error looking up ISBN', 'danger');
        }
        
        this.lookupIsbnBtn.disabled = false;
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize scanner when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BarcodeScanner();
});
