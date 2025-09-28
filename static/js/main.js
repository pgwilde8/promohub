// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh dashboard stats every 5 minutes
    if (window.location.pathname === '/dashboard') {
        setInterval(function() {
            // Subtle refresh without full page reload
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    console.log('Health check:', data.status);
                })
                .catch(error => console.error('Health check failed:', error));
        }, 300000); // 5 minutes
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                
                // Re-enable after 5 seconds to prevent permanent disable
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
                }, 5000);
            }
        });
    });
    
    // Store original button text
    const submitBtns = document.querySelectorAll('button[type="submit"]');
    submitBtns.forEach(btn => {
        btn.dataset.originalText = btn.innerHTML;
    });
    
    // Toast notifications
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    };
    
    function createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '11';
        document.body.appendChild(container);
        return container;
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Confirm dialogs for dangerous actions
    const dangerousButtons = document.querySelectorAll('[data-confirm]');
    dangerousButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.confirm;
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// Utility functions
window.formatDateTime = function(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
};

window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        window.showToast('Failed to copy', 'danger');
    });
};