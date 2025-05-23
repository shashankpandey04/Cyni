/**
 * Form Structure Utility
 * Handles parsing and preparation of the form structure for the application system
 */

class FormStructureManager {
    /**
     * Initialize the form structure manager
     * @param {string} formContainerId - The ID of the form container element
     * @param {string} hiddenInputId - The ID of the hidden input to store the form structure
     */
    constructor(formContainerId = 'sections-container', hiddenInputId = 'form-structure-input') {
        this.formContainer = document.getElementById(formContainerId);
        this.hiddenInput = document.getElementById(hiddenInputId);
    }

    /**
     * Generate form structure from the DOM
     * @returns {Object} The form structure object
     */
    generateFormStructure() {
        const formStructure = {
            sections: []
        };

        // Get all sections
        const sectionElements = this.formContainer.querySelectorAll('.section');
        
        sectionElements.forEach(sectionEl => {
            const titleInput = sectionEl.querySelector('input[name="section_title"]');
            const descInput = sectionEl.querySelector('input[name="section_description"]');
            
            const section = {
                title: titleInput ? titleInput.value : 'Untitled Section',
                description: descInput ? descInput.value : '',
                questions: []
            };
            
            // Get all questions in this section
            const questionElements = sectionEl.querySelectorAll('.question-item');
            
            questionElements.forEach(questionEl => {
                const questionInput = questionEl.querySelector('input[name="question"]');
                const typeSelect = questionEl.querySelector('select[name="question_type"]');
                const requiredToggle = questionEl.querySelector('.required-toggle');
                const optionsInput = questionEl.querySelector('.options-input');
                
                let options = [];
                if (optionsInput && !optionsInput.closest('.options-container').classList.contains('hidden')) {
                    options = optionsInput.value.split('\n').filter(opt => opt.trim() !== '');
                }
                
                const question = {
                    text: questionInput ? questionInput.value : 'Untitled Question',
                    type: typeSelect ? typeSelect.value : 'text',
                    required: requiredToggle ? requiredToggle.checked : false
                };
                
                // Add options if applicable
                if (['select', 'radio', 'checkbox', 'multiselect'].includes(question.type) && options.length > 0) {
                    question.options = options;
                }
                
                section.questions.push(question);
            });
            
            formStructure.sections.push(section);
        });
        
        return formStructure;
    }

    /**
     * Update the hidden input with the current form structure
     */
    updateHiddenInput() {
        if (this.hiddenInput) {
            const structure = this.generateFormStructure();
            this.hiddenInput.value = JSON.stringify(structure);
        }
    }

    /**
     * Set up form change listeners to update the hidden input
     */
    setupFormChangeListeners() {
        // Observe changes to the form structure
        const observer = new MutationObserver(() => this.updateHiddenInput());
        
        // Setup mutation observer on the form container
        observer.observe(this.formContainer, {
            childList: true,
            subtree: true,
            attributes: true,
            characterData: true
        });
        
        // Also listen for input changes
        this.formContainer.addEventListener('input', () => this.updateHiddenInput());
        this.formContainer.addEventListener('change', () => this.updateHiddenInput());
        
        // Initial update
        this.updateHiddenInput();
    }

    /**
     * Load an existing form structure into the DOM
     * @param {Object} structure - The form structure to load
     */
    loadExistingStructure(structure) {
        if (!structure || !structure.sections || !Array.isArray(structure.sections)) {
            console.error('Invalid form structure provided');
            return;
        }

        // Clear existing sections
        this.formContainer.innerHTML = '';

        // Add each section from structure
        structure.sections.forEach((section, index) => {
            // Create section element
            const sectionEl = document.createElement('div');
            sectionEl.className = 'section bg-zinc-800 rounded-lg p-4 border border-zinc-700';
            
            // Section header
            const sectionHeader = `
                <div class="section-header mb-4 flex justify-between items-center">
                    <div>
                        <input type="text" name="section_title" class="bg-transparent border-b border-zinc-600 text-white text-lg font-medium mb-1 focus:border-amber-500 focus:outline-none" 
                               placeholder="Section Title" value="${section.title || `Section ${index + 1}`}">
                        <input type="text" name="section_description" class="bg-transparent border-b border-zinc-600 text-gray-400 text-sm w-full focus:border-amber-500 focus:outline-none" 
                               placeholder="Section Description (optional)" value="${section.description || ''}">
                    </div>
                    <div class="flex items-center">
                        <button type="button" class="add-question p-1.5 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-white mr-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                        </button>
                        <button type="button" class="remove-section p-1.5 bg-red-500/20 hover:bg-red-500/40 rounded-lg text-red-400">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                        <div class="drag-handle ml-2 p-1 bg-zinc-700 rounded cursor-move">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                            </svg>
                        </div>
                    </div>
                </div>
            `;

            sectionEl.innerHTML = sectionHeader;

            // Create questions container
            const questionsContainer = document.createElement('div');
            questionsContainer.className = 'questions-container space-y-4 sortable-questions';
            
            // Add each question from section
            if (section.questions && Array.isArray(section.questions)) {
                section.questions.forEach(question => {
                    const questionItem = document.createElement('div');
                    questionItem.className = 'question-item bg-zinc-700/50 rounded-lg p-4 border border-zinc-600/50 relative';

                    // Prepare question markup
                    const hasOptions = ['select', 'radio', 'checkbox', 'multiselect'].includes(question.type);
                    const optionsValue = question.options ? question.options.join('\n') : '';

                    questionItem.innerHTML = `
                        <div class="flex items-start mb-3">
                            <input type="text" name="question" class="bg-transparent border-b border-zinc-600 text-white flex-grow mr-3 focus:border-amber-500 focus:outline-none" 
                                   placeholder="Enter a question" value="${question.text || ''}" required>
                            <select name="question_type" class="bg-zinc-900 border border-zinc-600 rounded px-2 py-1 text-sm text-white question-type-select">
                                <option value="text" ${question.type === 'text' ? 'selected' : ''}>Text Input</option>
                                <option value="number" ${question.type === 'number' ? 'selected' : ''}>Number Input</option>
                                <option value="select" ${question.type === 'select' ? 'selected' : ''}>Dropdown</option>
                                <option value="radio" ${question.type === 'radio' ? 'selected' : ''}>Radio Buttons</option>
                                <option value="checkbox" ${question.type === 'checkbox' ? 'selected' : ''}>Checkboxes</option>
                                <option value="multiselect" ${question.type === 'multiselect' ? 'selected' : ''}>Multi-select</option>
                            </select>
                            <div class="flex items-center ml-3">
                                <button type="button" class="remove-question p-1 hover:bg-red-500/20 rounded text-red-400">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                                <div class="drag-handle ml-2 p-1 bg-zinc-600 rounded cursor-move">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                        
                        <div class="options-container ${hasOptions ? '' : 'hidden'}">
                            <div class="mt-2 p-2 bg-zinc-800 rounded">
                                <div class="text-xs text-gray-400 mb-2">Options (one per line)</div>
                                <textarea class="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-white text-sm options-input" 
                                          placeholder="Option 1&#10;Option 2&#10;Option 3" rows="4">${optionsValue}</textarea>
                            </div>
                        </div>
                        
                        <div class="mt-2 text-xs text-gray-400 flex items-center">
                            <label class="flex items-center">
                                <input type="checkbox" class="required-toggle mr-1 bg-zinc-700 border-zinc-600" ${question.required ? 'checked' : ''}>
                                <span>Required</span>
                            </label>
                        </div>
                    `;
                    
                    questionsContainer.appendChild(questionItem);
                });
            }
            
            sectionEl.appendChild(questionsContainer);
            this.formContainer.appendChild(sectionEl);
        });

        // Update the hidden input with the loaded structure
        this.updateHiddenInput();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const formManager = new FormStructureManager();
    formManager.setupFormChangeListeners();
    
    // Update form structure when submitting the form
    const form = document.getElementById('applicationForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            formManager.updateHiddenInput();
        });
    }

    // Initialize existing form structure if available in the hidden input
    const hiddenInput = document.getElementById('form-structure-input');
    if (hiddenInput && hiddenInput.value) {
        try {
            const structure = JSON.parse(hiddenInput.value);
            if (structure) {
                formManager.loadExistingStructure(structure);
            }
        } catch(e) {
            console.error('Error parsing existing form structure:', e);
        }
    }
});
