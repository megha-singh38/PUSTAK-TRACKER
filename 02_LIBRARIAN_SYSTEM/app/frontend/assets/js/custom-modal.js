/**
 * Custom Modal System - Replaces ugly JS alerts/confirms
 * Provides beautiful, consistent modal dialogs
 */

class CustomModal {
    constructor() {
        this.createModalContainer();
    }

    createModalContainer() {
        // Remove existing modal if present
        const existing = document.getElementById('custom-modal-container');
        if (existing) {
            existing.remove();
        }

        // Create modal HTML
        const modalHTML = `
            <div class="modal fade" id="customModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header border-0 pb-0" id="customModalHeader">
                            <h5 class="modal-title d-flex align-items-center" id="customModalTitle">
                                <i class="bi me-2" id="customModalIcon"></i>
                                <span id="customModalTitleText"></span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="customModalBody">
                            <p id="customModalMessage" class="mb-0"></p>
                        </div>
                        <div class="modal-footer border-0 pt-0" id="customModalFooter">
                            <!-- Buttons will be added dynamically -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to body
        const container = document.createElement('div');
        container.id = 'custom-modal-container';
        container.innerHTML = modalHTML;
        document.body.appendChild(container);

        this.modalElement = document.getElementById('customModal');
        this.modal = new bootstrap.Modal(this.modalElement);
    }

    /**
     * Show an alert modal
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {string} title - Optional custom title
     */
    alert(message, type = 'info', title = null) {
        const config = this.getTypeConfig(type);
        
        // Set title
        document.getElementById('customModalTitleText').textContent = title || config.title;
        
        // Set icon
        const iconElement = document.getElementById('customModalIcon');
        iconElement.className = `bi ${config.icon} me-2`;
        
        // Set header color
        const header = document.getElementById('customModalHeader');
        header.className = `modal-header border-0 pb-0 ${config.headerClass}`;
        
        // Set message
        document.getElementById('customModalMessage').innerHTML = message;
        
        // Set footer with OK button
        const footer = document.getElementById('customModalFooter');
        footer.innerHTML = `
            <button type="button" class="btn ${config.buttonClass} px-4" data-bs-dismiss="modal">
                <i class="bi bi-check-lg me-1"></i> OK
            </button>
        `;
        
        this.modal.show();
    }

    /**
     * Show a confirm modal
     * @param {string} message - The message to display
     * @param {function} onConfirm - Callback when confirmed
     * @param {function} onCancel - Optional callback when cancelled
     * @param {string} type - Type: 'danger', 'warning', 'info'
     */
    confirm(message, onConfirm, onCancel = null, type = 'warning') {
        const config = this.getTypeConfig(type);
        
        // Set title
        document.getElementById('customModalTitleText').textContent = config.confirmTitle;
        
        // Set icon
        const iconElement = document.getElementById('customModalIcon');
        iconElement.className = `bi ${config.icon} me-2`;
        
        // Set header color
        const header = document.getElementById('customModalHeader');
        header.className = `modal-header border-0 pb-0 ${config.headerClass}`;
        
        // Set message
        document.getElementById('customModalMessage').innerHTML = message;
        
        // Set footer with Yes/No buttons
        const footer = document.getElementById('customModalFooter');
        footer.innerHTML = `
            <button type="button" class="btn btn-secondary px-4" id="customModalCancel">
                <i class="bi bi-x-lg me-1"></i> Cancel
            </button>
            <button type="button" class="btn ${config.buttonClass} px-4" id="customModalConfirm">
                <i class="bi bi-check-lg me-1"></i> Confirm
            </button>
        `;
        
        // Add event listeners
        document.getElementById('customModalConfirm').addEventListener('click', () => {
            this.modal.hide();
            if (onConfirm) onConfirm();
        });
        
        document.getElementById('customModalCancel').addEventListener('click', () => {
            this.modal.hide();
            if (onCancel) onCancel();
        });
        
        this.modal.show();
    }

    /**
     * Show a prompt modal
     * @param {string} message - The message to display
     * @param {function} onSubmit - Callback with input value
     * @param {string} defaultValue - Default input value
     * @param {string} placeholder - Input placeholder
     */
    prompt(message, onSubmit, defaultValue = '', placeholder = '') {
        // Set title
        document.getElementById('customModalTitleText').textContent = 'Input Required';
        
        // Set icon
        const iconElement = document.getElementById('customModalIcon');
        iconElement.className = 'bi bi-pencil-square me-2';
        
        // Set header color
        const header = document.getElementById('customModalHeader');
        header.className = 'modal-header border-0 pb-0 bg-light';
        
        // Set message with input
        document.getElementById('customModalMessage').innerHTML = `
            <p class="mb-3">${message}</p>
            <input type="text" class="form-control" id="customModalInput" 
                   value="${defaultValue}" placeholder="${placeholder}">
        `;
        
        // Set footer
        const footer = document.getElementById('customModalFooter');
        footer.innerHTML = `
            <button type="button" class="btn btn-secondary px-4" data-bs-dismiss="modal">
                <i class="bi bi-x-lg me-1"></i> Cancel
            </button>
            <button type="button" class="btn btn-primary px-4" id="customModalSubmit">
                <i class="bi bi-check-lg me-1"></i> Submit
            </button>
        `;
        
        // Add event listener
        const submitHandler = () => {
            const value = document.getElementById('customModalInput').value;
            this.modal.hide();
            if (onSubmit) onSubmit(value);
        };
        
        document.getElementById('customModalSubmit').addEventListener('click', submitHandler);
        
        // Allow Enter key to submit
        document.getElementById('customModalInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submitHandler();
        });
        
        this.modal.show();
        
        // Focus input after modal is shown
        this.modalElement.addEventListener('shown.bs.modal', () => {
            document.getElementById('customModalInput').focus();
        }, { once: true });
    }

    getTypeConfig(type) {
        const configs = {
            success: {
                title: 'Success',
                confirmTitle: 'Confirm Action',
                icon: 'bi-check-circle-fill',
                headerClass: 'bg-success bg-opacity-10',
                buttonClass: 'btn-success'
            },
            error: {
                title: 'Error',
                confirmTitle: 'Confirm Action',
                icon: 'bi-exclamation-circle-fill',
                headerClass: 'bg-danger bg-opacity-10',
                buttonClass: 'btn-danger'
            },
            warning: {
                title: 'Warning',
                confirmTitle: 'Confirm Action',
                icon: 'bi-exclamation-triangle-fill',
                headerClass: 'bg-warning bg-opacity-10',
                buttonClass: 'btn-warning'
            },
            danger: {
                title: 'Danger',
                confirmTitle: 'Are you sure?',
                icon: 'bi-trash-fill',
                headerClass: 'bg-danger bg-opacity-10',
                buttonClass: 'btn-danger'
            },
            info: {
                title: 'Information',
                confirmTitle: 'Confirm',
                icon: 'bi-info-circle-fill',
                headerClass: 'bg-info bg-opacity-10',
                buttonClass: 'btn-info'
            }
        };
        
        return configs[type] || configs.info;
    }
}

// Create global instance
let customModal;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        customModal = new CustomModal();
    });
} else {
    customModal = new CustomModal();
}

// Convenience functions
function showAlert(message, type = 'info', title = null) {
    if (!customModal) customModal = new CustomModal();
    customModal.alert(message, type, title);
}

function showConfirm(message, onConfirm, onCancel = null, type = 'warning') {
    if (!customModal) customModal = new CustomModal();
    customModal.confirm(message, onConfirm, onCancel, type);
}

function showPrompt(message, onSubmit, defaultValue = '', placeholder = '') {
    if (!customModal) customModal = new CustomModal();
    customModal.prompt(message, onSubmit, defaultValue, placeholder);
}

function showSuccess(message, title = 'Success') {
    showAlert(message, 'success', title);
}

function showError(message, title = 'Error') {
    showAlert(message, 'error', title);
}

function showWarning(message, title = 'Warning') {
    showAlert(message, 'warning', title);
}

function showInfo(message, title = 'Information') {
    showAlert(message, 'info', title);
}
