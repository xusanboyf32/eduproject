// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Password visibility toggle
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // File input preview
    document.querySelectorAll('.custom-file-input').forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Fayl tanlanmadi';
            const label = this.nextElementSibling;
            label.textContent = fileName;
            
            // Image preview
            if (this.files && this.files[0] && this.files[0].type.startsWith('image/')) {
                const reader = new FileReader();
                const preview = document.getElementById(this.dataset.preview);
                
                if (preview) {
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            }
        });
    });

    // Password strength meter
    const passwordInput = document.getElementById('id_password1');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strengthMeter = document.getElementById('password-strength-meter');
            const strengthText = document.getElementById('password-strength-text');
            
            if (strengthMeter && strengthText) {
                const strength = calculatePasswordStrength(password);
                
                // Update meter width and color
                strengthMeter.style.width = strength.score * 25 + '%';
                
                // Update meter color and text
                if (strength.score < 2) {
                    strengthMeter.className = 'progress-bar bg-danger';
                    strengthText.textContent = 'Juda zaif';
                } else if (strength.score < 3) {
                    strengthMeter.className = 'progress-bar bg-warning';
                    strengthText.textContent = 'Zaif';
                } else if (strength.score < 4) {
                    strengthMeter.className = 'progress-bar bg-info';
                    strengthText.textContent = 'Yaxshi';
                } else {
                    strengthMeter.className = 'progress-bar bg-success';
                    strengthText.textContent = 'Mustahkam';
                }
                
                // Show/hide feedback
                const feedback = document.getElementById('password-strength-feedback');
                if (feedback) {
                    feedback.innerHTML = '';
                    strength.feedback.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'small ' + (msg.valid ? 'text-success' : 'text-danger');
                        div.innerHTML = `<i class="fas fa-${msg.valid ? 'check' : 'times'} me-1"></i> ${msg.message}`;
                        feedback.appendChild(div);
                    });
                }
            }
        });
    }

    // Calculate password strength
    function calculatePasswordStrength(password) {
        let score = 0;
        const feedback = [];
        
        // Check length
        if (password.length >= 8) {
            score++;
            feedback.push({ valid: true, message: 'Minimal 8 ta belgi' });
        } else {
            feedback.push({ valid: false, message: 'Kamida 8 ta belgi bo\'lishi kerak' });
        }
        
        // Check for numbers
        if (/\d/.test(password)) {
            score++;
            feedback.push({ valid: true, message: 'Kamida 1 ta raqam mavjud' });
        } else {
            feedback.push({ valid: false, message: 'Kamida 1 ta raqam qo\'shing' });
        }
        
        // Check for uppercase letters
        if (/[A-Z]/.test(password)) {
            score++;
            feedback.push({ valid: true, message: 'Kamida 1 ta bosh harf mavjud' });
        } else {
            feedback.push({ valid: false, message: 'Kamida 1 ta bosh harf qo\'shing' });
        }
        
        // Check for special characters
        if (/[^A-Za-z0-9]/.test(password)) {
            score++;
            feedback.push({ valid: true, message: 'Maxsus belgi mavjud' });
        } else {
            feedback.push({ valid: false, message: 'Maxsus belgi qo\'shish tavsiya etiladi' });
        }
        
        return { score, feedback };
    }

    // Auto-hide success messages after 5 seconds
    setTimeout(() => {
        const messages = document.querySelectorAll('.alert-success');
        messages.forEach(message => {
            const alert = new bootstrap.Alert(message);
            alert.close();
        });
    }, 5000);

    // Handle dropdown submenus on hover
    const dropdowns = document.querySelectorAll('.dropdown-hover');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('mouseenter', function() {
            this.querySelector('.dropdown-menu').classList.add('show');
        });
        
        dropdown.addEventListener('mouseleave', function() {
            this.querySelector('.dropdown-menu').classList.remove('show');
        });
    });

    // Initialize select2 if available
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $('select[data-toggle="select2"]').select2({
            theme: 'bootstrap-5',
            width: '100%'
        });
    }

    // Handle file upload preview
    document.querySelectorAll('.file-upload-preview').forEach(uploader => {
        const input = uploader.querySelector('input[type="file"]');
        const preview = uploader.querySelector('.file-preview');
        const removeBtn = uploader.querySelector('.remove-file');
        
        if (input && preview) {
            input.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        if (preview.tagName === 'IMG') {
                            preview.src = e.target.result;
                        } else {
                            preview.innerHTML = `
                                <div class="d-flex align-items-center">
                                    <i class="fas fa-file-pdf fa-2x text-danger me-2"></i>
                                    <div>
                                        <div class="fw-bold">${input.files[0].name}</div>
                                        <small class="text-muted">${(input.files[0].size / 1024).toFixed(1)} KB</small>
                                    </div>
                                </div>
                            `;
                        }
                        preview.classList.remove('d-none');
                        
                        if (removeBtn) {
                            removeBtn.classList.remove('d-none');
                        }
                    };
                    
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
        
        if (removeBtn) {
            removeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                if (input) {
                    input.value = '';
                    
                    // Reset file input (for IE11)
                    input.type = '';
                    input.type = 'file';
                }
                
                if (preview) {
                    if (preview.tagName === 'IMG') {
                        preview.src = '';
                    } else {
                        preview.innerHTML = '';
                    }
                    preview.classList.add('d-none');
                }
                
                this.classList.add('d-none');
            });
        }
    });

    // Initialize datepickers
    if (typeof $ !== 'undefined' && $.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'dd.mm.yyyy',
            autoclose: true,
            todayHighlight: true,
            language: 'ru'
        });
    }

    // Handle sidebar toggle for mobile
    const sidebarToggler = document.querySelector('.sidebar-toggler');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggler && sidebar) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Handle click outside to close sidebar on mobile
    document.addEventListener('click', function(event) {
        if (sidebar && sidebarToggler) {
            const isClickInside = sidebar.contains(event.target) || sidebarToggler.contains(event.target);
            
            if (!isClickInside && sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        }
    });

    // Handle active nav links
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
            
            // Also activate parent dropdown if exists
            const parentDropdown = link.closest('.dropdown');
            if (parentDropdown) {
                const dropdownToggle = parentDropdown.querySelector('.dropdown-toggle');
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                }
            }
        }
    });
});

// Utility function to show loading state
function showLoading(button, text = 'Yuklanmoqda...') {
    if (!button) return;
    
    button.disabled = true;
    const originalHtml = button.innerHTML;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        ${text}
    `;
    
    return function() {
        button.disabled = false;
        button.innerHTML = originalHtml;
    };
}

// Utility function to show toast notifications
function showToast(options) {
    const { title, message, type = 'info', duration = 5000 } = options;
    
    const toastContainer = document.getElementById('toast-container') || (() => {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        return container;
    })();
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${title ? `<strong>${title}</strong><br>` : ''}
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
    
    return {
        hide: () => bsToast.hide(),
        dispose: () => bsToast.dispose()
    };
}

// Handle AJAX forms with file uploads
function handleAjaxForm(form, options = {}) {
    if (!form) return;
    
    const { onSuccess, onError, onComplete } = options;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        const resetLoading = submitButton ? showLoading(submitButton) : null;
        
        fetch(form.action || window.location.href, {
            method: form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (onSuccess) {
                onSuccess(data);
            } else {
                // Default success handler
                showToast({
                    title: 'Muvaffaqiyatli!',
                    message: data.message || 'Amaliyot muvaffaqiyatli bajarildi',
                    type: 'success'
                });
                
                // Reset form if needed
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1500);
                } else if (data.reset_form) {
                    form.reset();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            if (onError) {
                onError(error);
            } else {
                // Default error handler
                showToast({
                    title: 'Xatolik!',
                    message: error.message || 'Xatolik yuz berdi. Iltimos, qaytadan urinib ko\'ring.',
                    type: 'danger'
                });
            }
        })
        .finally(() => {
            if (resetLoading) resetLoading();
            if (onComplete) onComplete();
        });
    });
}

// Utility function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize all AJAX forms
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
        handleAjaxForm(form);
    });
});
