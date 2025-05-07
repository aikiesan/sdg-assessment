// js/assessment/main_assessment.js
// Main script for SDG Expert Assessment Tool - Orchestration & Core Logic

// --- Constants ---
const SDG_INFO = {
    1:  { name: 'No Poverty',                 color: '#E5243B', icon: 'fa-hand-holding-usd' },
    2:  { name: 'Zero Hunger',                color: '#DDA63A', icon: 'fa-seedling' },
    3:  { name: 'Good Health & Well-being',   color: '#4C9F38', icon: 'fa-heartbeat' },
    4:  { name: 'Quality Education',          color: '#C5192D', icon: 'fa-graduation-cap' },
    5:  { name: 'Gender Equality',            color: '#FF3A21', icon: 'fa-venus-mars' },
    6:  { name: 'Clean Water & Sanitation',   color: '#26BDE2', icon: 'fa-tint' },
    7:  { name: 'Affordable & Clean Energy',  color: '#FCC30B', icon: 'fa-bolt' },
    8:  { name: 'Decent Work & Economic Growth', color: '#A21942', icon: 'fa-briefcase' },
    9:  { name: 'Industry, Innovation & Infrastructure', color: '#FD6925', icon: 'fa-industry' },
    10: { name: 'Reduced Inequalities',       color: '#DD1367', icon: 'fa-arrows-alt-h' }, // Simplified icon
    11: { name: 'Sustainable Cities & Communities', color: '#FD9D24', icon: 'fa-city' },
    12: { name: 'Responsible Consumption & Production', color: '#BF8B2E', icon: 'fa-recycle' },
    13: { name: 'Climate Action',             color: '#3F7E44', icon: 'fa-cloud-sun-rain' },
    14: { name: 'Life Below Water',           color: '#0A97D9', icon: 'fa-water' },
    15: { name: 'Life on Land',               color: '#56C02B', icon: 'fa-tree' },
    16: { name: 'Peace, Justice & Strong Institutions', color: '#00689D', icon: 'fa-landmark' },
    17: { name: 'Partnerships for the Goals', color: '#19486A', icon: 'fa-handshake' }
};
const TOTAL_SDGS = 17;

// --- State Variables ---
let currentSectionId = 'sdg-1'; // Initial section
const assessmentData = {}; // Stores user inputs { sdg-1: { inputs: {...}, notes: '' }, ... }
const visitedSections = new Set(['sdg-1']); // Track visited sections

// --- DOM Elements (declared globally, assigned after DOM loaded) ---
let form;
let sectionsContainer;
let allSections;
let progressBar;
let progressText;
let indicatorContainer;
let resultsSection;
let assessmentDataInput;
let sdgBreakdownContainer;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    // Assign DOM Elements
    form = document.getElementById('sdg-assessment-form');
    sectionsContainer = document.getElementById('sdg-sections');
    allSections = document.querySelectorAll('.sdg-section');
    progressBar = document.getElementById('progress-bar');
    progressText = document.getElementById('progress-text');
    indicatorContainer = document.getElementById('sdg-indicator-container');
    resultsSection = document.getElementById('results-section');
    assessmentDataInput = document.getElementById('assessment-data');
    sdgBreakdownContainer = document.getElementById('sdg-breakdown-details');

    // Add auto-fill button listener
    const autoFillBtn = document.getElementById('auto-fill-btn');
    if (autoFillBtn) {
        autoFillBtn.addEventListener('click', autoFillTestData);
    }

    // First, ensure all sections exist and are properly set up
    const initializeSections = () => {
        // Hide all sections initially
        allSections.forEach(section => {
            if (section.id !== 'sdg-1') {
                section.classList.add('hidden');
            }
        });

        // Verify all SDG sections exist
        for (let i = 1; i <= TOTAL_SDGS; i++) {
            const sectionId = `sdg-${i}`;
            const section = document.getElementById(sectionId);
            if (!section) {
                console.error(`Section ${sectionId} not found in the DOM`);
                continue;
            }

            // Ensure proper class setup
            section.classList.add('sdg-section');
            if (i !== 1) {
                section.classList.add('hidden');
            }

            // Add navigation event listeners
            const nextBtn = section.querySelector('.next-btn');
            const prevBtn = section.querySelector('.prev-btn');

            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    const nextId = nextBtn.getAttribute('data-next');
                    if (nextId && document.getElementById(nextId)) {
                        saveCurrentSectionData();
                        showSection(nextId);
                    } else {
                        console.error(`Next section ${nextId} not found`);
                    }
                });
            }

            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    const prevId = prevBtn.getAttribute('data-prev');
                    if (prevId && document.getElementById(prevId)) {
                        saveCurrentSectionData();
                        showSection(prevId);
                    } else {
                        console.error(`Previous section ${prevId} not found`);
                    }
                });
            }
        }
    };

    // Load language preference or default
    const savedLang = localStorage.getItem('sdgAssessmentLang') || 'en';
    // Ensure i18n functions/data are available before calling UI updates
    if (typeof setLanguage === 'function') {
        setLanguage(savedLang); // Apply language
    } else {
        console.error("setLanguage function not found. i18n script might be missing or failed to load.");
    }

    // Initialize sections first
    initializeSections();

    // Then initialize UI components that depend on language being set
    if (typeof generateIndicatorButtons === 'function') {
        generateIndicatorButtons();
    } else {
        console.error("generateIndicatorButtons function not found. UI script might be missing.");
    }

    if (typeof setupEventListeners === 'function') {
        setupEventListeners();
    } else {
        console.error("setupEventListeners function not found. UI script might be missing.");
    }

    // Show first section and update progress
    const firstSection = document.getElementById('sdg-1');
    if (firstSection) {
        firstSection.classList.remove('hidden');
        if (typeof updateProgress === 'function') {
            updateProgress();
        }
        if (typeof updateIndicatorButtons === 'function') {
            updateIndicatorButtons();
        }
    }

    // Setup Submit Button Listener here as it calls functions from multiple modules
    const submitButton = document.getElementById('submit-assessment');
    if (submitButton) {
        submitButton.addEventListener('click', handleAssessmentCompletion);
    } else {
        console.warn("Submit button not found.");
    }

    console.log("Expert Assessment Initialized (main_assessment.js)");
});

// --- Core Functions ---

function saveCurrentSectionData() {
    const currentSectionElement = document.getElementById(currentSectionId);
    if (!currentSectionElement) return;

    const sectionData = {
        inputs: {}, // Store values by name/id
        notes: ''
    };

    const inputs = currentSectionElement.querySelectorAll('input[type="checkbox"], input[type="radio"], input[type="text"], textarea');

    inputs.forEach(input => {
         const name = input.name || input.id;
         if (!name) return;

         switch (input.type) {
             case 'checkbox':
                 if (!sectionData.inputs[name]) sectionData.inputs[name] = [];
                 if (input.checked) {
                     sectionData.inputs[name].push(input.value);
                 }
                 break;
             case 'radio':
                 if (input.checked) {
                     sectionData.inputs[name] = input.value;
                 }
                 break;
             case 'text':
             case 'textarea':
                if (name.endsWith('_notes')) {
                     sectionData.notes = input.value.trim();
                } else {
                   sectionData.inputs[name] = input.value.trim();
                }
                 break;
         }
    });

    // Clean up empty arrays for checkboxes
    Object.keys(sectionData.inputs).forEach(key => {
       if (Array.isArray(sectionData.inputs[key]) && sectionData.inputs[key].length === 0) {
           delete sectionData.inputs[key];
       }
    });

    // Store in main assessment object
    assessmentData[currentSectionId] = sectionData;

    // Update hidden input
    if (assessmentDataInput) {
        assessmentDataInput.value = JSON.stringify(assessmentData);
    }

    // Save progress to server
    const projectId = document.querySelector('input[name="project_id"]').value;
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    // Create save data object
    const saveData = {
        project_id: projectId,
        section_id: currentSectionId,
        section_data: sectionData,
        csrf_token: csrfToken
    };

    // Show saving indicator
    const savingIndicator = document.createElement('div');
    savingIndicator.className = 'fixed bottom-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
    savingIndicator.textContent = 'Saving progress...';
    document.body.appendChild(savingIndicator);

    // Make AJAX request to save progress
    fetch('/api/save-progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(saveData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Save failed: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(`Saved data for ${currentSectionId}:`, data);
        savingIndicator.textContent = 'Progress saved';
        savingIndicator.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        setTimeout(() => {
            savingIndicator.remove();
        }, 2000);
    })
    .catch(error => {
        console.error('Error saving progress:', error);
        savingIndicator.textContent = 'Error saving progress. Changes will be saved when you submit.';
        savingIndicator.className = 'fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        setTimeout(() => {
            savingIndicator.remove();
        }, 3000);
    });

    // Update indicator button style
    if(typeof updateIndicatorButtons === 'function') {
        updateIndicatorButtons();
    }
}

function handleAssessmentCompletion() {
     console.log("Completing assessment...");
     saveCurrentSectionData(); // Save the last section's data

     // --- Score Calculation (call function from scoring_assessment.js) ---
     let calculatedScores = [];
     if (typeof calculateAllSdgScores === 'function') {
        calculatedScores = calculateAllSdgScores(assessmentData);
        console.log("Calculated Scores:", calculatedScores);
     } else {
        console.error("calculateAllSdgScores function not found. Scoring script might be missing.");
        alert("Error: Could not calculate scores.");
        return;
     }

     // --- Display Results (call function from ui_assessment.js) ---
      if (typeof displayResults === 'function') {
        displayResults(calculatedScores);
     } else {
        console.error("displayResults function not found. UI script might be missing.");
        alert("Error: Could not display results.");
     }
}

// Add auto-fill functionality
function autoFillTestData() {
    try {
        // Helper functions
        const setInputValue = (sectionId, inputName, value) => {
            const section = document.getElementById(sectionId);
            if (!section) return;
            const input = section.querySelector(`[name="${inputName}"]`);
            if (input) {
                input.value = value;
            }
        };

        const checkCheckboxes = (sectionId, inputName, values) => {
            const section = document.getElementById(sectionId);
            if (!section) return;
            const checkboxes = section.querySelectorAll(`[name="${inputName}"]`);
            checkboxes.forEach(checkbox => {
                if (values.includes(checkbox.value)) {
                    checkbox.checked = true;
                }
            });
        };

        const setRadioValue = (sectionId, inputName, value) => {
            const section = document.getElementById(sectionId);
            if (!section) return;
            const radio = section.querySelector(`[name="${inputName}"][value="${value}"]`);
            if (radio) {
                radio.checked = true;
            }
        };

        // Fill test data for each SDG
        // SDG 1
        setRadioValue('sdg-1', 'sdg1_cost_reduction', 'cost_reduc_3');
        setInputValue('sdg-1', 'sdg1_baseline_cost', 'Baseline: $500/month, Project: $167/month');
        setInputValue('sdg-1', 'sdg1_notes', 'Implemented solar panels and improved insulation for significant cost reduction.');

        // SDG 2
        setRadioValue('sdg-2', 'sdg2_food_integration', 'community');
        setInputValue('sdg-2', 'sdg2_notes', 'Added community garden with educational programs and composting facilities.');

        // SDG 3
        checkCheckboxes('sdg-3', 'sdg3_actions', ['materials', 'air_quality', 'water_quality', 'lighting_quality', 'acoustic_comfort']);
        setRadioValue('sdg-3', 'sdg3_health_summary', '5');
        setInputValue('sdg-3', 'sdg3_notes', 'Used low-VOC materials, HEPA filters, UV water treatment, and acoustic insulation.');

        // Continue for SDGs 4-17...
        // Add similar test data for remaining SDGs

        console.log('Test data auto-filled successfully');
    } catch (error) {
        console.error('Error auto-filling test data:', error);
    }
}