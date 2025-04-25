/**
 * multi-page-assessment.js - JavaScript for multi-page SDG Assessment Form
 * Handles validation, auto-save, and state management across assessment steps
 */

// Use IIFE to prevent global scope pollution
(function() {
    // DOM elements cache
    const elements = {
        form: document.getElementById('sdg-assessment-form'),
        nextButton: document.querySelector('.btn-next'),
        prevButton: document.querySelector('.btn-prev'),
        progressBar: document.querySelector('.progress-bar'),
        progressText: document.querySelector('.progress-bar-text'),
        radioInputs: document.querySelectorAll('input[type="radio"]'),
        textareas: document.querySelectorAll('.evidence-field'),
        csrfToken: document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                   document.querySelector('input[name="csrf_token"]')?.value
    };
    
    // Extract step information from the URL
    const currentUrl = window.location.pathname;
    const stepMatch = currentUrl.match(/step(\d+)/);
    const currentStep = stepMatch ? parseInt(stepMatch[1]) : 1;
    
    // Extract project and assessment IDs from form data attributes
    const projectId = elements.form ? elements.form.getAttribute('data-project-id') : null;
    const assessmentId = elements.form ? elements.form.getAttribute('data-assessment-id') : null;
    
    // Auto-save timer 
    let saveTimer = null;
    
    // Debounce delay in ms
    const DEBOUNCE_DELAY = 2000;
    
    // Form modified flag
    let formModified = false;
    
    /**
     * Initialize the form functionality
     */
    function init() {
        if (!elements.form) {
            console.log('Form not found');
            return;
        }
        
        console.log('Initializing multi-page assessment form');
        
        // Ensure CSRF token is present in form
        refreshCSRFToken();
        
        // Add event listeners
        addEventListeners();
        
        // Set up auto-save
        initAutoSave();
        
        // Try to load saved data if available
        loadSavedData();
        
        // Update progress indicator
        updateProgress();
        
        // Handle unsaved changes warning
        setupBeforeUnloadWarning();
        
        // For debugging
        console.log('Current step:', currentStep);
        console.log('Project ID:', projectId);
        console.log('Assessment ID:', assessmentId);
    }
    
    /**
     * Refresh CSRF token in the form and update local reference
     */
    function refreshCSRFToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        const formToken = document.querySelector('input[name="csrf_token"]')?.value;
        const currentToken = metaToken || formToken;
        
        if (!currentToken) {
            console.warn('CSRF token not found in document');
            return;
        }
        
        // Update our reference
        elements.csrfToken = currentToken;
        
        // Update or create token input in form
        if (elements.form) {
            let tokenInput = elements.form.querySelector('input[name="csrf_token"]');
            if (!tokenInput) {
                tokenInput = document.createElement('input');
                tokenInput.type = 'hidden';
                tokenInput.name = 'csrf_token';
                elements.form.appendChild(tokenInput);
            }
            tokenInput.value = currentToken;
        }
    }
    
    /**
     * Add event listeners to form elements
     */
    function addEventListeners() {
        console.log('Adding event listeners');
        
        // Form submission - this handles both the Save & Continue button and other submit events
        if (elements.form) {
            elements.form.addEventListener('submit', function(e) {
                console.log('Form submit event detected');
                
                // Prevent default submission temporarily
                e.preventDefault();
                
                // Save form data immediately before submitting
                saveFormDataImmediately();
                
                // Ensure CSRF token is up to date
                refreshCSRFToken();
                
                // Set the submission flag to prevent beforeunload warning
                window.isFormSubmitting = true;
                
                // Submit the form after ensuring CSRF token is present
                setTimeout(() => this.submit(), 50);
            });
        }
        
        // Listen for radio button changes to track completion
        elements.radioInputs.forEach(radio => {
            radio.addEventListener('change', function() {
                formModified = true;
                updateProgress();
            });
        });
        
        // Evidence field input changes
        elements.textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                formModified = true;
                const charCount = document.getElementById(`charCount_${this.dataset.id}`);
                if (charCount) {
                    charCount.textContent = this.value.length;
                }
                
                // If using evidence quality meter, update it
                updateEvidenceQuality(this);
            });
            
            // Initial update
            textarea.dispatchEvent(new Event('input'));
        });
    }
    
    /**
     * Save form data immediately (non-debounced version for form submission)
     */
    function saveFormDataImmediately() {
        try {
            // Serialize form data
            const formData = serializeForm();
            
            // Save to localStorage
            saveToLocalStorage(formData);
            
            // Track completed SDGs
            updateCompletionStatus();
            
            // Reset modified flag
            formModified = false;
            
            console.log('Form data saved before submission');
        } catch (error) {
            console.error('Error saving form data:', error);
        }
    }
    
    /**
     * Validate the current step
     * @returns {boolean} - Whether step is valid
     */
    function validateCurrentStep() {
        let isValid = true;
        
        try {
            // Check required fields
            const requiredFields = elements.form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (field.type === 'radio') {
                    // For radio buttons, check if any in the group is selected
                    const name = field.name;
                    const checked = elements.form.querySelector(`input[name="${name}"]:checked`);
                    if (!checked) {
                        isValid = false;
                        highlightInvalidField(field.closest('.rating-options'));
                    }
                } else if (!field.value.trim()) {
                    isValid = false;
                    highlightInvalidField(field);
                }
            });
        } catch (error) {
            console.error('Validation error:', error);
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Create and show validation error message
     * @param {string} message - Error message to display
     */
    function showValidationError(message = "Please complete all required fields before proceeding.") {
        // Create or get the error element
        let error = document.getElementById('validation-error');
        if (!error) {
            error = document.createElement('div');
            error.id = 'validation-error';
            error.className = 'alert alert-danger alert-dismissible fade show mt-3';
            error.innerHTML = `
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            elements.form.prepend(error);
        } else {
            error.innerHTML = `
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            error.classList.add('show');
        }
        
        // Scroll to error
        error.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    /**
     * Highlight invalid field with error styling
     * @param {HTMLElement} field - Field to highlight
     */
    function highlightInvalidField(field) {
        if (!field) return;
        
        field.classList.add('is-invalid');
        
        // Add event listener to remove invalid class when field is corrected
        const removeInvalidOnInput = function() {
            field.classList.remove('is-invalid');
            field.removeEventListener('input', removeInvalidOnInput);
            field.removeEventListener('change', removeInvalidOnInput);
        };
        
        field.addEventListener('input', removeInvalidOnInput);
        field.addEventListener('change', removeInvalidOnInput);
    }
    
    /**
     * Update progress indicator based on completed fields
     */
    function updateProgress() {
        if (!elements.progressBar || !elements.progressText) {
            console.log('Progress elements not found');
            return;
        }
        
        try {
            // Get total assessable SDGs based on your assessment structure
            const sdgsByStep = {
                1: 4,   // Step 1: SDGs 1, 2, 3, 6
                2: 4,   // Step 2: SDGs 4, 5, 8, 10
                3: 4,   // Step 3: SDGs 7, 9, 11, 12
                4: 3,   // Step 4: SDGs 13, 14, 15
                5: 2    // Step 5: SDGs 16, 17
            };
            
            const totalSDGs = Object.values(sdgsByStep).reduce((sum, count) => sum + count, 0);
            
            // Count completed SDGs across all steps
            const completedSDGs = loadCompletionStatus();
            
            // Calculate completion percentage
            const completionPercentage = Math.round((completedSDGs.length / totalSDGs) * 100);
            
            // Update progress bar
            elements.progressBar.style.width = `${completionPercentage}%`;
            elements.progressBar.setAttribute('aria-valuenow', completionPercentage);
            
            // Update progress text
            elements.progressText.textContent = `${completionPercentage}% (${completedSDGs.length}/${totalSDGs} SDGs rated)`;
            
            // Update progress bar color based on completion
            if (completionPercentage < 25) {
                elements.progressBar.className = 'progress-bar bg-danger';
            } else if (completionPercentage < 50) {
                elements.progressBar.className = 'progress-bar bg-warning';
            } else if (completionPercentage < 100) {
                elements.progressBar.className = 'progress-bar bg-info';
            } else {
                elements.progressBar.className = 'progress-bar bg-success';
            }
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }
    
    /**
     * Initialize auto-save functionality
     */
    function initAutoSave() {
        try {
            // Set up input change listeners
            const formInputs = elements.form.querySelectorAll('input, textarea, select');
            
            formInputs.forEach(input => {
                input.addEventListener('change', debounce(saveFormData, DEBOUNCE_DELAY));
                
                // For text inputs and textareas, also listen for input events
                if (input.type === 'text' || input.tagName.toLowerCase() === 'textarea') {
                    input.addEventListener('input', debounce(saveFormData, DEBOUNCE_DELAY));
                }
            });
            
            console.log('Auto-save initialized');
        } catch (error) {
            console.error('Error initializing auto-save:', error);
        }
    }
    
    /**
     * Create a debounce function to prevent excessive calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} - Debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Save form data to localStorage and update completion status
     */
    function saveFormData() {
        try {
            // Serialize form data
            const formData = serializeForm();
            
            // Save to localStorage
            saveToLocalStorage(formData);
            
            // Show save indicator
            showSaveIndicator('Auto-saved');
            
            // Track completed SDGs
            updateCompletionStatus();
            
            // Reset modified flag
            formModified = false;
            
            console.log('Form data auto-saved');
        } catch (error) {
            console.error('Error saving form data:', error);
            showSaveIndicator('Save failed', 'error');
        }
    }
    
    /**
     * Serialize form data into an object
     * @returns {Object} - Serialized form data
     */
    function serializeForm() {
        const formData = {};
        
        // Add current CSRF token to ensure it's saved
        if (elements.csrfToken) {
            formData.csrf_token = elements.csrfToken;
        }
        
        try {
            const inputs = elements.form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                // Don't duplicate the csrf_token
                if (input.name === 'csrf_token') return;
                
                if (input.type === 'radio') {
                    if (input.checked) {
                        formData[input.name] = input.value;
                    }
                } else if (input.type === 'checkbox') {
                    formData[input.name] = input.checked;
                } else {
                    formData[input.name] = input.value;
                }
            });
        } catch (error) {
            console.error('Error serializing form:', error);
        }
        
        return formData;
    }
    
    /**
     * Save form data to localStorage
     * @param {Object} formData - Form data to save
     */
    function saveToLocalStorage(formData) {
        try {
            // Use a step-specific key to store data for each step separately
            const storageKey = `sdg_assessment_${projectId || 'new'}_step${currentStep}`;
            localStorage.setItem(storageKey, JSON.stringify({
                timestamp: new Date().toISOString(),
                data: formData
            }));
        } catch (error) {
            console.error('LocalStorage save failed:', error);
        }
    }
    
    /**
     * Load saved form data from localStorage
     */
    function loadSavedData() {
        try {
            const storageKey = `sdg_assessment_${projectId || 'new'}_step${currentStep}`;
            const savedData = localStorage.getItem(storageKey);
            
            if (savedData) {
                const parsedData = JSON.parse(savedData);
                
                // Check if saved data is recent enough (within 24 hours)
                const savedTime = new Date(parsedData.timestamp).getTime();
                const currentTime = new Date().getTime();
                const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
                
                if (currentTime - savedTime <= maxAge) {
                    // Restore form data
                    populateForm(parsedData.data);
                    showSaveIndicator('Loaded saved data', 'info');
                    
                    // Always refresh the CSRF token after loading saved data
                    refreshCSRFToken();
                    
                    // Update completion tracking after loading data
                    updateCompletionStatus();
                    
                    console.log('Saved data loaded successfully');
                } else {
                    // Data is too old, remove it
                    localStorage.removeItem(storageKey);
                    console.log('Saved data was too old and has been removed');
                }
            } else {
                console.log('No saved data found for this step');
            }
        } catch (error) {
            console.error('Error loading saved data:', error);
        }
    }
    
    /**
     * Populate form with saved data
     * @param {Object} formData - Form data to populate
     */
    function populateForm(formData) {
        try {
            Object.keys(formData).forEach(key => {
                // Skip the CSRF token field - we'll handle it separately
                if (key === 'csrf_token') return;
                
                const inputs = elements.form.querySelectorAll(`[name="${key}"]`);
                
                inputs.forEach(input => {
                    if (input.type === 'radio') {
                        input.checked = (input.value === formData[key]);
                    } else if (input.type === 'checkbox') {
                        input.checked = formData[key];
                    } else {
                        input.value = formData[key];
                        
                        // Trigger input event for textareas to update char count and quality meter
                        if (input.tagName.toLowerCase() === 'textarea') {
                            input.dispatchEvent(new Event('input'));
                        }
                    }
                });
            });
        } catch (error) {
            console.error('Error populating form:', error);
        }
    }
    
    /**
     * Update completion status in localStorage
     */
    function updateCompletionStatus() {
        try {
            // Get completed SDGs from current form
            const completedSdgs = [];
            elements.radioInputs.forEach(radio => {
                if (radio.checked && radio.value !== '0') {
                    // Extract SDG number from name (assumed format: score_X where X is SDG ID)
                    const sdgMatch = radio.name.match(/score_(\d+)/);
                    if (sdgMatch && sdgMatch[1]) {
                        completedSdgs.push(sdgMatch[1]);
                    }
                }
            });
            
            // Get existing completion status
            const completionKey = `sdg_assessment_${projectId || 'new'}_completion`;
            const existingData = localStorage.getItem(completionKey);
            let completionData = existingData ? JSON.parse(existingData) : {};
            
            // Store completion data for this step
            completionData[`step${currentStep}`] = completedSdgs;
            
            // Save updated completion data
            localStorage.setItem(completionKey, JSON.stringify(completionData));
            
            console.log(`Updated completion status: ${completedSdgs.length} SDGs completed in this step`);
        } catch (error) {
            console.error('Error updating completion status:', error);
        }
    }
    
    /**
     * Load completion status from localStorage
     * @returns {Array} - Array of completed SDG IDs
     */
    function loadCompletionStatus() {
        try {
            const completionKey = `sdg_assessment_${projectId || 'new'}_completion`;
            const existingData = localStorage.getItem(completionKey);
            if (!existingData) return [];
            
            // Combine completed SDGs from all steps
            const completionData = JSON.parse(existingData);
            let allCompletedSdgs = [];
            
            Object.values(completionData).forEach(stepSdgs => {
                if (Array.isArray(stepSdgs)) {
                    allCompletedSdgs = [...allCompletedSdgs, ...stepSdgs];
                }
            });
            
            // Remove duplicates
            return [...new Set(allCompletedSdgs)];
        } catch (error) {
            console.error('Error loading completion status:', error);
            return [];
        }
    }
    
    /**
     * Clear all saved data from localStorage
     */
    function clearSavedData() {
        try {
            // Clear step-specific data
            for (let step = 1; step <= 5; step++) {
                const stepKey = `sdg_assessment_${projectId || 'new'}_step${step}`;
                localStorage.removeItem(stepKey);
            }
            
            // Clear completion data
            const completionKey = `sdg_assessment_${projectId || 'new'}_completion`;
            localStorage.removeItem(completionKey);
            
            console.log('All saved assessment data cleared');
        } catch (error) {
            console.error('Error clearing saved data:', error);
        }
    }
    
    /**
     * Set up warning for unsaved changes
     */
    function setupBeforeUnloadWarning() {
        window.addEventListener('beforeunload', function(e) {
            if (formModified && !window.isFormSubmitting) {
                const message = 'You have unsaved changes. Are you sure you want to leave?';
                e.returnValue = message;
                return message;
            }
        });
        
        // Flag for tracking form submission
        if (elements.form) {
            elements.form.addEventListener('submit', function() {
                window.isFormSubmitting = true;
            });
        }
        
        console.log('Unsaved changes warning set up');
    }
    
    /**
     * Create and show a save indicator
     * @param {string} message - Message to display
     * @param {string} type - Indicator type (success, error, info)
     */
    function showSaveIndicator(message = 'Saved', type = 'success') {
        let indicator = document.getElementById('save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'save-indicator';
            document.body.appendChild(indicator);
            
            // Add styles for the indicator
            if (!document.getElementById('save-indicator-style')) {
                const style = document.createElement('style');
                style.id = 'save-indicator-style';
                style.textContent = `
                    #save-indicator {
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        padding: 10px 15px;
                        border-radius: 4px;
                        color: white;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                        z-index: 9999;
                        opacity: 0;
                        transform: translateY(20px);
                        transition: opacity 0.3s, transform 0.3s;
                    }
                    
                    #save-indicator.show {
                        opacity: 1;
                        transform: translateY(0);
                    }
                    
                    #save-indicator.success {
                        background-color: rgba(40, 167, 69, 0.9);
                    }
                    
                    #save-indicator.error {
                        background-color: rgba(220, 53, 69, 0.9);
                    }
                    
                    #save-indicator.info {
                        background-color: rgba(13, 110, 253, 0.9);
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // Set appropriate styling based on type
        indicator.className = '';
        indicator.classList.add(type);
        
        // Set message
        indicator.textContent = message;
        
        // Show indicator
        indicator.classList.add('show');
        
        // Hide after 2 seconds
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }
    
    /**
     * Update evidence quality meter
     * @param {HTMLElement} field - Evidence field
     */
    function updateEvidenceQuality(field) {
        if (!field) return;
        
        try {
            const id = field.getAttribute('data-id');
            const qualityMeter = document.getElementById(`quality_${id}`);
            
            if (!qualityMeter) return;
            
            const levelElement = qualityMeter.querySelector('.evidence-level');
            const textElement = qualityMeter.querySelector('.evidence-text');
            
            if (levelElement) {
                const count = field.value.length;
                const maxLength = field.getAttribute('maxlength') || 500;
                const percentage = Math.min(100, (count / maxLength) * 100);
                
                levelElement.style.width = `${percentage}%`;
                
                if (textElement) {
                    let qualityText = 'Not started';
                    
                    if (count > 0) {
                        if (count < 50) {
                            qualityText = 'Minimal evidence';
                        } else if (count < 150) {
                            qualityText = 'Basic evidence';
                        } else if (count < 300) {
                            qualityText = 'Good evidence';
                        } else if (count < 450) {
                            qualityText = 'Strong evidence';
                        } else {
                            qualityText = 'Comprehensive evidence';
                        }
                    }
                    
                    textElement.textContent = `Evidence strength: ${qualityText}`;
                }
            }
        } catch (error) {
            console.error('Error updating evidence quality:', error);
        }
    }
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', init);
    
    // Expose API for other scripts
    window.SDGAssessmentForm = {
        validateCurrentStep,
        saveProgress: saveFormDataImmediately,
        clearSavedData,
        refreshCSRFToken
    };
})();
