/**
 * assessment-form.js - JavaScript for multi-step SDG Assessment Form
 * Handles navigation, validation, auto-save, and submission for the SDG assessment process
 */

// Use IIFE to prevent global scope pollution
(function() {
    // DOM elements cache
    const elements = {
        form: document.getElementById('sdg-assessment-form'),
        sections: document.querySelectorAll('.assessment-section'),
        nextButtons: document.querySelectorAll('.btn-next'),
        prevButtons: document.querySelectorAll('.btn-prev'),
        progressBar: document.querySelector('.progress-bar'),
        progressText: document.querySelector('.progress-bar-text'),
        saveIndicator: document.getElementById('save-indicator') || createSaveIndicator(),
        radioInputs: document.querySelectorAll('input[type="radio"]'),
        textareas: document.querySelectorAll('.evidence-field')
    };
    
    // Current section tracker
    let currentSection = 0;
    // Auto-save timer
    let saveTimer = null;
    // Debounce delay in ms
    const DEBOUNCE_DELAY = 2000;
    // Form modified flag
    let formModified = false;
    // Project ID from data attribute
    const projectId = elements.form ? elements.form.getAttribute('data-project-id') : null;
    // Assessment ID from data attribute (if editing)
    const assessmentId = elements.form ? elements.form.getAttribute('data-assessment-id') : null;
    
    /**
     * Initialize the form functionality
     */
    function init() {
        if (!elements.form) return;

        // Add event listeners
        addEventListeners();
        
        // Show the first section
        showSection(0);
        
        // Update progress indicator
        updateProgress();
        
        // Set up auto-save
        initAutoSave();
        
        // Try to load saved data if available
        loadSavedData();
        
        // Setup form submission
        setupFormSubmission();
        
        // Add beforeunload warning if form is modified
        window.addEventListener('beforeunload', function(e) {
            if (formModified) {
                const message = 'You have unsaved changes. Are you sure you want to leave?';
                e.returnValue = message;
                return message;
            }
        });
    }
    
    /**
     * Add event listeners to all form elements
     */
    function addEventListeners() {
        // Next button clicks
        elements.nextButtons.forEach(button => {
            button.addEventListener('click', handleNextClick);
        });
        
        // Previous button clicks
        elements.prevButtons.forEach(button => {
            button.addEventListener('click', handlePrevClick);
        });
        
        // Listen for radio button changes to track completion
        elements.radioInputs.forEach(radio => {
            radio.addEventListener('change', function() {
                formModified = true;
                updateProgress();
                highlightCompletedSections();
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
                updateEvidenceQuality(this);
            });
            
            // Initial update
            textarea.dispatchEvent(new Event('input'));
        });
    }
    
    /**
     * Handle next button click
     * @param {Event} e - Click event
     */
    function handleNextClick(e) {
        e.preventDefault();
        const sectionIndex = parseInt(e.target.getAttribute('data-section'));
        
        // Validate current section before proceeding
        if (validateSection(sectionIndex)) {
            showSection(sectionIndex + 1);
            updateProgress();
            saveFormData(); // Save progress when moving to next section
        } else {
            showValidationError("Please complete all required fields before continuing.");
        }
    }
    
    /**
     * Handle previous button click
     * @param {Event} e - Click event
     */
    function handlePrevClick(e) {
        e.preventDefault();
        const sectionIndex = parseInt(e.target.getAttribute('data-section'));
        showSection(sectionIndex - 1);
        updateProgress();
    }
    
    /**
     * Show a specific section and hide others
     * @param {number} index - Section index to show
     */
    function showSection(index) {
        if (index < 0 || index >= elements.sections.length) return;
        
        elements.sections.forEach((section, i) => {
            if (i === index) {
                section.classList.add('active');
                section.style.display = 'block';
            } else {
                section.classList.remove('active');
                section.style.display = 'none';
            }
        });
        
        currentSection = index;
        
        // Scroll to top of section
        window.scrollTo({
            top: elements.form.offsetTop - 100,
            behavior: 'smooth'
        });
    }
    
    /**
     * Validate the current section
     * @param {number} sectionIndex - Section index to validate
     * @returns {boolean} - Whether section is valid
     */
    function validateSection(sectionIndex) {
        if (sectionIndex < 0 || sectionIndex >= elements.sections.length) return false;
        
        const section = elements.sections[sectionIndex];
        let isValid = true;
        
        // Check required fields
        const requiredFields = section.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (field.type === 'radio') {
                // For radio buttons, check if any in the group is selected
                const name = field.name;
                const checked = section.querySelector(`input[name="${name}"]:checked`);
                if (!checked) {
                    isValid = false;
                highlightInvalidField(field);
            }
        });
        
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
            elements.sections[currentSection].prepend(error);
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
        if (!elements.progressBar || !elements.progressText) return;
        
        // Count selected radio buttons (each SDG should have one selected option)
        const totalSDGs = document.querySelectorAll('.sdg-card').length;
        const completedSDGs = document.querySelectorAll('input[type="radio"]:checked').length;
        
        // Calculate completion percentage
        const completionPercentage = Math.round((completedSDGs / totalSDGs) * 100);
        
        // Update progress bar
        elements.progressBar.style.width = `${completionPercentage}%`;
        elements.progressBar.setAttribute('aria-valuenow', completionPercentage);
        
        // Update progress text
        elements.progressText.textContent = `${completionPercentage}% (${completedSDGs}/${totalSDGs} SDGs rated)`;
        
        // Update color based on completion
        if (completionPercentage < 25) {
            elements.progressBar.classList.remove('bg-success', 'bg-warning', 'bg-info');
            elements.progressBar.classList.add('bg-danger');
        } else if (completionPercentage < 50) {
            elements.progressBar.classList.remove('bg-success', 'bg-danger', 'bg-info');
            elements.progressBar.classList.add('bg-warning');
        } else if (completionPercentage < 100) {
            elements.progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
            elements.progressBar.classList.add('bg-info');
        } else {
            elements.progressBar.classList.remove('bg-info', 'bg-warning', 'bg-danger');
            elements.progressBar.classList.add('bg-success');
        }
    }
    
    /**
     * Highlight completed sections in the navigation
     */
    function highlightCompletedSections() {
        // Implementation depends on your navigation structure
        const sectionNavItems = document.querySelectorAll('.section-nav-item');
        if (!sectionNavItems.length) return;
        
        elements.sections.forEach((section, index) => {
            const navItem = sectionNavItems[index];
            if (!navItem) return;
            
            const requiredFields = section.querySelectorAll('[required]');
            let sectionComplete = true;
            
            requiredFields.forEach(field => {
                if (field.type === 'radio') {
                    // For radio buttons, check if any in the group is selected
                    const name = field.name;
                    const checked = section.querySelector(`input[name="${name}"]:checked`);
                    if (!checked) {
                        sectionComplete = false;
                    }
                } else if (!field.value.trim()) {
                    sectionComplete = false;
                }
            });
            
            if (sectionComplete) {
                navItem.classList.add('completed');
                navItem.querySelector('.section-status')?.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            } else {
                navItem.classList.remove('completed');
                navItem.querySelector('.section-status')?.innerHTML = '<i class="bi bi-circle text-muted"></i>';
            }
        });
    }
    
    /**
     * Initialize auto-save functionality
     */
    function initAutoSave() {
        // Set up input change listeners
        const formInputs = elements.form.querySelectorAll('input, textarea, select');
        
        formInputs.forEach(input => {
            input.addEventListener('change', debounce(saveFormData, DEBOUNCE_DELAY));
            
            // For text inputs and textareas, also listen for input events
            if (input.type === 'text' || input.type === 'textarea') {
                input.addEventListener('input', debounce(saveFormData, DEBOUNCE_DELAY));
            }
        });
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
     * Save form data to localStorage (and optionally to server via AJAX)
     */
    function saveFormData() {
        try {
            // Serialize form data
            const formData = serializeForm();
            
            // Save to localStorage
            saveToLocalStorage(formData);
            
            // Save to server (if assessment exists)
            if (assessmentId) {
                saveToServer(formData);
            }
            
            // Show save indicator
            showSaveIndicator('Auto-saved');
            
            // Reset modified flag
            formModified = false;
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
        const inputs = elements.form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
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
        
        return formData;
    }
    
    /**
     * Save form data to localStorage
     * @param {Object} formData - Form data to save
     */
    function saveToLocalStorage(formData) {
        try {
            const storageKey = `sdg_assessment_${projectId}_${assessmentId || 'new'}`;
            localStorage.setItem(storageKey, JSON.stringify({
                timestamp: new Date().toISOString(),
                data: formData
            }));
        } catch (error) {
            console.error('LocalStorage save failed:', error);
            // Consider fallback options here
        }
    }
    
    /**
     * Save form data to server via AJAX
     * @param {Object} formData - Form data to save
     */
    function saveToServer(formData) {
        // Only proceed if we have an assessment ID
        if (!assessmentId) return;
        
        const url = `/assessments/${assessmentId}/save-draft`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Draft saved successfully:', data);
            // Could update UI here if needed
        })
        .catch(error => {
            console.error('Error saving draft to server:', error);
            // Consider retry logic here
        });
    }
    
    /**
     * Load saved form data from localStorage
     */
    function loadSavedData() {
        try {
            const storageKey = `sdg_assessment_${projectId}_${assessmentId || 'new'}`;
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
                    showSaveIndicator('Loaded saved draft', 'info');
                    
                    // Update progress after loading data
                    updateProgress();
                    highlightCompletedSections();
                } else {
                    // Data is too old, remove it
                    localStorage.removeItem(storageKey);
                }
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
        Object.keys(formData).forEach(key => {
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
    }
    
    /**
     * Setup form submission handler
     */
    function setupFormSubmission() {
        if (!elements.form) return;
        
        elements.form.addEventListener('submit', function(e) {
            // Prevent default submission
            e.preventDefault();
            
            // Validate all sections before submission
            let allValid = true;
            
            elements.sections.forEach((section, index) => {
                if (!validateSection(index)) {
                    allValid = false;
                }
            });
            
            if (allValid) {
                // Show submission indicator
                showSaveIndicator('Submitting assessment...', 'info');
                
                // Clear localStorage data
                if (projectId) {
                    const storageKey = `sdg_assessment_${projectId}_${assessmentId || 'new'}`;
                    localStorage.removeItem(storageKey);
                }
                
                // Submit the form
                this.submit();
            } else {
                // Find the first invalid section and navigate to it
                let firstInvalidSection = 0;
                for (let i = 0; i < elements.sections.length; i++) {
                    if (!validateSection(i)) {
                        firstInvalidSection = i;
                        break;
                    }
                }
                
                showSection(firstInvalidSection);
                showValidationError("Please complete all required fields before submitting.");
                
                // Scroll to the first invalid field in this section
                const firstInvalidField = elements.sections[firstInvalidSection].querySelector('.is-invalid');
                if (firstInvalidField) {
                    firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }
    
    /**
     * Create and show a save indicator
     * @param {string} message - Message to display
     * @param {string} type - Indicator type (success, error, info)
     */
    function showSaveIndicator(message = 'Saved', type = 'success') {
        let indicator = elements.saveIndicator;
        
        // Set appropriate styling based on type
        indicator.className = 'save-indicator';
        
        if (type === 'error') {
            indicator.classList.add('save-indicator-error');
        } else if (type === 'info') {
            indicator.classList.add('save-indicator-info');
        } else {
            indicator.classList.add('save-indicator-success');
        }
        
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
     * Create save indicator element if it doesn't exist
     * @returns {HTMLElement} - Save indicator element
     */
    function createSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'save-indicator';
        indicator.className = 'save-indicator';
        indicator.textContent = 'Saved';
        document.body.appendChild(indicator);
        
        // Add styles for the indicator
        const style = document.createElement('style');
        style.textContent = `
            .save-indicator {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: rgba(40, 167, 69, 0.9);
                color: white;
                padding: 10px 15px;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 9999;
                opacity: 0;
                transform: translateY(20px);
                transition: opacity 0.3s, transform 0.3s;
            }
            
            .save-indicator.show {
                opacity: 1;
                transform: translateY(0);
            }
            
            .save-indicator-error {
                background-color: rgba(220, 53, 69, 0.9);
            }
            
            .save-indicator-info {
                background-color: rgba(13, 110, 253, 0.9);
            }
        `;
        document.head.appendChild(style);
        
        return indicator;
    }
    
    /**
     * Update evidence quality meter
     * Delegates to the existing function in assessment.js if available
     * @param {HTMLElement} field - Evidence field
     */
    function updateEvidenceQuality(field) {
        const id = field.getAttribute('data-id');
        const qualityMeter = document.getElementById(`quality_${id}`);
        
        if (!qualityMeter) return;
        
        // Use existing function if available
        if (window.SDGAssessmentUtils && typeof window.SDGAssessmentUtils.updateEvidenceQualityMeter === 'function') {
            window.SDGAssessmentUtils.updateEvidenceQualityMeter(
                qualityMeter, 
                field.value.length, 
                field.getAttribute('maxlength')
            );
        } else {
            // Simple fallback implementation
            const count = field.value.length;
            const maxLength = field.getAttribute('maxlength') || 500;
            const percentage = Math.min(100, (count / maxLength) * 100);
            
            const levelElement = qualityMeter.querySelector('.evidence-level');
            if (levelElement) {
                levelElement.style.width = `${percentage}%`;
            }
        }
    }
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', init);
    
    // Expose API for other scripts
    window.SDGAssessmentForm = {
        goToSection: showSection,
        validateCurrentSection: () => validateSection(currentSection),
        saveProgress: saveFormData,
        validateAll: () => {
            let allValid = true;
            elements.sections.forEach((section, index) => {
                if (!validateSection(index)) {
                    allValid = false;
                }
            });
            return allValid;
        }
    };
})();
                    highlightInvalidField(field.closest('.rating-options'));
                }
            } else if (!field.value.trim()) {
                isValid = false;