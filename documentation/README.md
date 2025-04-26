# SDG Assessment Toolkit for Architecture Projects

## Overview
The SDG Assessment Toolkit is a digital platform developed for architects and urban planners to evaluate their projects against the United Nations Sustainable Development Goals (SDGs). Initiated by the International Union of Architects (UIA), the toolkit aims to foster sustainable practices in the built environment by providing a standardized, user-friendly, and secure assessment method.

## Project Goals
- Enable architects to measure and visualize their project's alignment with the SDGs.
- Lower the barrier for SDG assessment through an intuitive questionnaire.
- Ensure data security and GDPR compliance, with user data controlled by UIA.
- Support global accessibility through multilingual features.
- Allow for phased development, including future AI-powered analytics.

## Key Features
- **User-Friendly Questionnaire:** Tailored for architecture projects, guiding users through SDG-relevant topics.
- **Real-Time Analysis:** Immediate feedback and visual representation of SDG alignment.
- **Secure Data Handling:** GDPR-compliant storage, explicit user consent, and privacy controls.
- **Modular & Scalable:** Designed for phased implementation and future feature expansion (e.g., AI analysis, new project types).
- **Multilingual Support:** Planned support for English, French, Spanish, Portuguese, and Chinese.
- **Continuous Updates:** Toolkit designed for ongoing improvement based on user and expert feedback.

## Technical Architecture
- **Backend:** Python (Flask), modular structure (`models`, `routes`, `services`, `utils`).
- **Frontend:** Jinja2 templates, Bootstrap for responsive UI, HTML5/CSS3/JS.
- **Database:** SQLite (development), with migration scripts for easy updates.
- **Security:** User authentication, privacy policy, and terms of use templates; GDPR compliance planned at both policy and technical levels.
- **Testing:** Automated tests in the `tests/` directory.

## Security & GDPR Compliance
- User data is stored securely and will not be used for commercial purposes.
- GDPR features: explicit consent, right to erasure, and secure hosting (UIA-controlled).
- Privacy and terms pages are included; technical compliance (encryption, consent flows) is being implemented.

## Phased Implementation & Roadmap
1. **Phase 1:** Core toolkit (questionnaire, results, user management, privacy policies), pilot testing.
2. **Phase 2:** Feature expansion (AI analytics, additional SDG modules, new project types).
3. **Phase 3:** Full-scale deployment, global rollout, integration with partners (e.g., UN-Habitat).

## User Guide
### Getting Started
1. Register or log in to the platform.
2. Create a new project and fill out the SDG assessment questionnaire.
3. Submit responses to receive a visual analysis of your project’s SDG alignment.
4. Review feedback and identify areas for improvement.
5. Access your dashboard to manage projects and assessments.

### Privacy & Data Control
- Users must accept privacy policy and terms before submitting data.
- Data can be deleted upon user request (GDPR right to erasure).

## Contribution & Partnership
- Feedback from architects, planners, and sustainability experts is welcome.
- Partners can assist with translations, funding, outreach, and integration with other sustainability initiatives.
- To contribute, please contact the project team or submit issues/PRs (if open source).

## Future Vision
- AI-powered analysis to identify sustainability trends and best practices.
- Expansion to cover public space, social housing, and other specialized domains.
- Presentation at international events and collaboration with global organizations.

## Contact & Support
- **Lead Developer:** Lucas (UIA Technical Expert)
- **Project Team:** Rui (Secretary General, UIA), Carla, Yves, Patrick, and other UIA members
- For questions or collaboration, contact the UIA or the project team via the official UIA website.

---

*This toolkit is a work in progress. Your feedback is crucial to making it a global standard for sustainable architecture assessment.*
