// js/assessment/i18n_assessment.js
// Handles internationalization (translations)

let currentLanguage = 'en'; // Default language

const translations = {
    en: {
        // General translations
        page_title: "SDG Expert Assessment",
        header_title: "SDG Expert Assessment Tool",
        header_subtitle: "Sustainable Architecture & Urban Planning Framework",
        progress_title: "Assessment Progress",
        progress_status: "SDG {current} of {total}",
        score_label: "Score",
        continue_button: "Continue to SDG {next}",
        back_button: "Back to SDG {prev}",
        print_button: "Print Results",
        download_button: "Download PDF",
        restart_button: "Start New Assessment",
        auto_fill_button: 'Auto-fill Test Data',

        // Performance levels
        perf_excellent: "Excellent",
        perf_good: "Good",
        perf_fair: "Fair",
        perf_needs_improvement: "Needs Improvement",

        // SDG Titles (for chart tooltips and breakdown)
        sdg1_title: "No Poverty",
        sdg2_title: "Zero Hunger",
        sdg3_title: "Good Health & Well-being",
        sdg4_title: "Quality Education",
        sdg5_title: "Gender Equality",
        sdg6_title: "Clean Water & Sanitation",
        sdg7_title: "Affordable & Clean Energy",
        sdg8_title: "Decent Work & Economic Growth",
        sdg9_title: "Industry, Innovation & Infrastructure",
        sdg10_title: "Reduced Inequalities",
        sdg11_title: "Sustainable Cities & Communities",
        sdg12_title: "Responsible Consumption & Production",
        sdg13_title: "Climate Action",
        sdg14_title: "Life Below Water",
        sdg15_title: "Life on Land",
        sdg16_title: "Peace, Justice & Strong Institutions",
        sdg17_title: "Partnerships for the Goals"
    },
    fr: {
        // French translations would go here
        // Add them as needed
        auto_fill_button: 'Remplir avec données test',
    }
};

// Function to translate all elements with data-translate-key attributes
function translatePage() {
    const elements = document.querySelectorAll('[data-translate-key]');
    elements.forEach(element => {
        const key = element.getAttribute('data-translate-key');
        if (translations[currentLanguage] && translations[currentLanguage][key]) {
            // Handle different element types
            if (element.tagName === 'INPUT' && (element.type === 'text' || element.type === 'textarea')) {
                element.placeholder = translations[currentLanguage][key];
            } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                // For other input types, update title/aria-label
                element.title = translations[currentLanguage][key];
            } else {
                element.textContent = translations[currentLanguage][key];
            }
        }
    });
}

// Function to set the current language and update the UI
function setLanguage(lang) {
    if (!translations[lang]) {
        console.error(`Language ${lang} is not supported.`);
        return;
    }

    // Update current language
    currentLanguage = lang;
    
    // Save preference to localStorage
    localStorage.setItem('sdgAssessmentLang', lang);
    
    // Update language buttons if they exist
    document.querySelectorAll('.lang-btn').forEach(btn => {
        const btnLang = btn.getAttribute('data-lang');
        if (btnLang === lang) {
            btn.classList.add('active', 'bg-white/20');
        } else {
            btn.classList.remove('active', 'bg-white/20');
        }
    });

    // Translate the page
    translatePage();

    // Removed updateIndicatorButtons call as it's only needed on the assessment page
    // if (typeof updateIndicatorButtons === 'function') {
    //     updateIndicatorButtons();
    // }

    // Update navigation button text if the function is available
    if (typeof updateNavigationButtonText === 'function') {
        updateNavigationButtonText();
    }

    console.log(`Language set to: ${lang}`);
}

// Initialize with saved language preference or default
document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('sdgAssessmentLang') || 'en';
    setLanguage(savedLang);
});

// Export the translations object
if (typeof module !== 'undefined' && module.exports) {
    module.exports = translations;
}