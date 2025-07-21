// Premium Modal Functions
function showPremiumModal() {
    const modal = document.getElementById('premiumModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Re-initialize lucide icons in the modal
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

// Initialize premium modal functionality
document.addEventListener('DOMContentLoaded', function() {
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
});

// AutoMod Settings JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Handle keyword deletion confirmation
    const deleteKeywordButtons = document.querySelectorAll('button[name="delete_keyword"]');
    deleteKeywordButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const keyword = this.getAttribute('data-keyword') || this.previousElementSibling?.textContent;
            if (!confirm(`Are you sure you want to delete the keyword "${keyword}"?`)) {
                e.preventDefault();
            }
        });
    });

    // Handle domain deletion confirmation
    const deleteDomainButtons = document.querySelectorAll('button[name="delete_domain"]');
    deleteDomainButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const domain = this.getAttribute('data-domain') || this.parentElement?.querySelector('span')?.textContent;
            if (!confirm(`Are you sure you want to remove the domain "${domain}"?`)) {
                e.preventDefault();
            }
        });
    });

    // Form validation for adding keywords
    const addKeywordForm = document.querySelector('form');
    if (addKeywordForm) {
        const keywordInput = addKeywordForm.querySelector('input[name="new_keyword"]');
        const addKeywordButton = addKeywordForm.querySelector('button[name="add_keyword"]');
        
        if (keywordInput && addKeywordButton) {
            addKeywordButton.addEventListener('click', function(e) {
                const keyword = keywordInput.value.trim();
                if (!keyword) {
                    e.preventDefault();
                    alert('Please enter a keyword to add.');
                    keywordInput.focus();
                }
            });
        }
    }

    // Form validation for adding domains
    if (addKeywordForm) {
        const domainInput = addKeywordForm.querySelector('input[name="new_domain"]');
        const addDomainButton = addKeywordForm.querySelector('button[name="add_domain"]');
        
        if (domainInput && addDomainButton) {
            addDomainButton.addEventListener('click', function(e) {
                const domain = domainInput.value.trim();
                if (!domain) {
                    e.preventDefault();
                    alert('Please enter a domain to add.');
                    domainInput.focus();
                } else if (!isValidDomain(domain)) {
                    e.preventDefault();
                    alert('Please enter a valid domain (e.g., example.com).');
                    domainInput.focus();
                }
            });
        }
    }
});

// Utility function to validate domain format
function isValidDomain(domain) {
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
    return domainRegex.test(domain) || domain.includes('.');
}

// Auto-save functionality for settings (optional enhancement)
function enableAutoSave() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const selects = document.querySelectorAll('select');
    const numberInputs = document.querySelectorAll('input[type="number"]');
    
    [...checkboxes, ...selects, ...numberInputs].forEach(input => {
        input.addEventListener('change', function() {
            // Show saving indicator
            showSavingIndicator();
            
            // Auto-save after a delay
            setTimeout(() => {
                // This could trigger an AJAX save request
                hideSavingIndicator();
            }, 1000);
        });
    });
}

function showSavingIndicator() {
    // Implementation for showing a saving indicator
    console.log('Saving changes...');
}

function hideSavingIndicator() {
    // Implementation for hiding the saving indicator
    console.log('Changes saved.');
}
