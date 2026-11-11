/**
 * Speech-to-Text Simulation Utility for the Patient Voice Terminal.
 * Simulates real-time transcription latency, audio wave extraction,
 * and AI summarization in Kannada and English.
 */

export interface SpeechScenario {
  id: string;
  label: string;
  transcriptEn: string;
  transcriptKn: string;
  summaryEn: string;
  summaryKn: string;
  wardEn: string;
  wardKn: string;
  departmentEn: string;
  departmentKn: string;
  category: string;
  priority: 'Routine' | 'Urgent' | 'Emergency';
  isEmergency?: boolean;
}

export const PRESET_SCENARIOS: SpeechScenario[] = [
  {
    id: 'water',
    label: 'Facility: Drinking Water Filter Leaking',
    transcriptEn: 'The drinking water dispenser on 3rd floor Ward B is empty and leaking water all over the floor.',
    transcriptKn: '3ನೇ ಮಹಡಿಯ ವಾರ್ಡ್ ಬಿ ನಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಫಿಲ್ಟರ್ ಖಾಲಿಯಾಗಿದೆ ಮತ್ತು ನೆಲದ ಮೇಲೆ ನೀರು ಸೋರುತ್ತಿದೆ.',
    summaryEn: 'Drinking water dispenser empty and leaking on 3rd floor corridor.',
    summaryKn: '3ನೇ ಮಹಡಿಯ ಕಾರಿಡಾರ್‌ನಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಫಿಲ್ಟರ್ ಖಾಲಿಯಾಗಿದೆ ಮತ್ತು ಸೋರುತ್ತಿದೆ.',
    wardEn: 'General Ward 3B (3rd Floor)',
    wardKn: 'ಜನರಲ್ ವಾರ್ಡ್ 3B (3ನೇ ಮಹಡಿ)',
    departmentEn: 'Sanitation & Facility Maintenance',
    departmentKn: 'ನೈರ್ಮಲ್ಯ ಮತ್ತು ಸೌಲಭ್ಯ ನಿರ್ವಹಣೆ',
    category: 'Facility & Cleanliness',
    priority: 'Routine',
  },
  {
    id: 'nurse',
    label: 'Nursing: Unattended Patient with Fever',
    transcriptEn: 'The patient on Bed 14 has had a rising high fever since afternoon, and the call bell was pressed 4 times without any nurse attending.',
    transcriptKn: 'ಬೆಡ್ 14 ರ ರೋಗಿಗೆ ಮಧ್ಯಾಹ್ನದಿಂದ ತೀವ್ರ ಜ್ವರ ಬಂದಿದೆ, 4 ಬಾರಿ ಬೆಲ್ ಒತ್ತಿದರೂ ಯಾವುದೇ ದಾದಿಯರು (ನರ್ಸ್) ಬಂದಿಲ್ಲ.',
    summaryEn: 'Call bell unattended for patient with high fever on Bed 14.',
    summaryKn: 'ಬೆಡ್ 14 ರ ತೀವ್ರ ಜ್ವರದ ರೋಗಿಯ ಕರೆ ಗಂಟೆಗೆ ಸಿಬ್ಬಂದಿ ಸ್ಪಂದಿಸಿಲ್ಲ.',
    wardEn: 'Medical Inpatient Ward (Bed 14)',
    wardKn: 'ಮೆಡಿಕಲ್ ವಾರ್ಡ್ (ಬೆಡ್ 14)',
    departmentEn: 'Inpatient Nursing Care',
    departmentKn: 'ಒಳರೋಗಿಗಳ ಶುಶ್ರೂಷಾ ವಿಭಾಗ',
    category: 'Patient Care',
    priority: 'Urgent',
  },
  {
    id: 'emergency-chest-pain',
    label: '🚨 EMERGENCY: Severe Chest Pain / Heart Attack',
    transcriptEn: 'My elderly father is sweating heavily, clutching his chest, and cannot breathe! He is having a heart attack right now!',
    transcriptKn: 'ನನ್ನ ತಂದೆಗೆ ಎದೆ ತುಂಬಾ ನೋಯುತ್ತಿದೆ, ಬೆವರು ಬರುತ್ತಿದೆ, ಉಸಿರಾಟ ನಿಲ್ಲುತ್ತಿದೆ! ಹಾರ್ಟ್ ಅಟ್ಯಾಕ್ (ಹೃದಯಾಘಾತ) ಆಗಿದೆ, ಬೇಗ ಬನ್ನಿ!',
    summaryEn: 'CRITICAL EMERGENCY: Severe acute chest pain and cardiac distress.',
    summaryKn: 'ತುರ್ತು ಅಪಾಯ: ತೀವ್ರ ಎದೆ ನೋವು ಮತ್ತು ಹೃದಯಾಘಾತದ ಲಕ್ಷಣಗಳು.',
    wardEn: 'OPD Waiting Lounge (Ground Floor)',
    wardKn: 'ಒಪಿಡಿ ಕಾಯುವ ಕೊಠಡಿ (ನೆಲಮಹಡಿ)',
    departmentEn: 'Casualty / Emergency Resuscitation',
    departmentKn: 'ತುರ್ತು ಚಿಕಿತ್ಸಾ ವಿಭಾಗ (ಕ್ಯಾಶುಯಲ್ಟಿ)',
    category: 'Life-Threatening Emergency',
    priority: 'Emergency',
    isEmergency: true,
  },
];

/**
 * Simulates asynchronous voice recognition and entity extraction processing delay.
 */
export const simulateSpeechProcessing = (delayMs: number = 2200): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
};
