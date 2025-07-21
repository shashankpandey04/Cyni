// Premium Modal Functions
function showPremiumModal() {
    const modal = document.getElementById('premiumModal');
    if (modal) {
        modal.classList.remove('hidden');
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

function closePremiumModal() {
    const modal = document.getElementById('premiumModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Show notification function
function showNotification(message, type = 'success') {
    // Remove existing notifications
    const existingNotifs = document.querySelectorAll('.automod-notification');
    existingNotifs.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = `automod-notification fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 transform translate-x-0 ${
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'error' ? 'bg-red-500 text-white' : 
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// AJAX Toggle Handler - Only for main enable/disable toggles
function handleToggleChange(checkbox, actionType) {
    const isEnabled = checkbox.checked;
    const guildId = window.location.pathname.split('/')[2];
    
    console.log('Toggle changed:', actionType, 'enabled:', isEnabled, 'guildId:', guildId);
    
    // Show loading state
    const toggleContainer = checkbox.closest('label');
    if (toggleContainer) {
        toggleContainer.style.opacity = '0.6';
        toggleContainer.style.pointerEvents = 'none';
    }
    
    fetch(`/dashboard/${guildId}/settings/automod/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            action_type: actionType,
            enabled: isEnabled
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Show/hide the settings section based on toggle state
            const settingsSection = checkbox.closest('.glass-effect').querySelector('.p-6');
            if (settingsSection) {
                if (isEnabled) {
                    settingsSection.style.display = 'block';
                    settingsSection.style.opacity = '1';
                } else {
                    settingsSection.style.opacity = '0.5';
                }
            }
        } else {
            // Revert toggle state on error
            checkbox.checked = !isEnabled;
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Revert toggle state on error
        checkbox.checked = !isEnabled;
        showNotification('An error occurred. Please try again.', 'error');
    })
    .finally(() => {
        // Restore normal state
        if (toggleContainer) {
            toggleContainer.style.opacity = '1';
            toggleContainer.style.pointerEvents = 'auto';
        }
    });
}

// Initialize AutoMod functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('AutoMod JavaScript loaded');
    
    // Handle premium modal
    const modal = document.getElementById('premiumModal');
    if (modal) {
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closePremiumModal();
            }
        });

        // Close modal with escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closePremiumModal();
            }
        });
    }
    
    // Initialize toggle switches with AJAX - ONLY for main toggles
    const toggles = {
        'raid_enabled': 'raid_detection',
        'spam_enabled': 'spam_detection',
        'keyword_enabled': 'custom_keyword',
        'link_enabled': 'link_blocking',
        'vanity_enabled': 'vanity_protection'
    };
    
    console.log('Setting up main toggles:', toggles);
    
    Object.entries(toggles).forEach(([inputName, actionType]) => {
        const toggle = document.querySelector(`input[name="${inputName}"]`);
        if (toggle) {
            console.log('Found main toggle:', inputName, toggle);
            
            // Remove any existing onchange attributes
            toggle.removeAttribute('onchange');
            
            // Add new event listener for AJAX toggle
            toggle.addEventListener('change', function() {
                console.log('Main toggle clicked:', inputName, this.checked);
                handleToggleChange(this, actionType);
            });
        } else {
            console.warn('Main toggle not found:', inputName);
        }
    });
    
    // Handle regular form submissions (for settings, not main toggles)
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitter = e.submitter;
            
            // Only handle form submission if it's NOT a main toggle
            if (submitter && submitter.type === 'submit') {
                console.log('Form submitted via button:', submitter.name, submitter.value);
                
                // Show loading state on the submit button
                if (submitter.name === 'action_type' || submitter.name === 'add_keyword' || submitter.name === 'add_domain') {
                    submitter.disabled = true;
                    const originalText = submitter.innerHTML;
                    submitter.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 mr-2 inline animate-spin"></i>Saving...';
                    
                    // Re-enable after a delay (form will redirect anyway)
                    setTimeout(() => {
                        submitter.disabled = false;
                        submitter.innerHTML = originalText;
                        if (typeof lucide !== 'undefined') {
                            lucide.createIcons();
                        }
                    }, 2000);
                }
            }
        });
    });
    
    // Handle keyword deletion confirmation
    const deleteKeywordButtons = document.querySelectorAll('button[name="delete_keyword"]');
    deleteKeywordButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const keyword = this.closest('.flex')?.querySelector('span')?.textContent;
            if (!confirm(`Are you sure you want to delete the keyword "${keyword}"?`)) {
                e.preventDefault();
            }
        });
    });

    // Handle domain deletion confirmation
    const deleteDomainButtons = document.querySelectorAll('button[onclick*="delete_domain"]');
    deleteDomainButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const domain = this.closest('.flex')?.querySelector('span')?.textContent;
            if (!confirm(`Are you sure you want to delete the domain "${domain}"?`)) {
                e.preventDefault();
            }
        });
    });
    
    console.log('AutoMod JavaScript initialization complete');
});
