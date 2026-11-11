/**
 * Emergency Redirection & Detection Logic for Patient Terminal.
 * Identifies life-threatening medical keywords in speech (English and Kannada)
 * and bypasses standard grievance registration to redirect immediately to Casualty.
 */

export const EMERGENCY_KEYWORDS = [
  'heart attack',
  'chest pain',
  'severe pain',
  'unconscious',
  'heavy bleeding',
  'difficulty breathing',
  'breathing failure',
  'stroke',
  'ಹಾರ್ಟ್ ಅಟ್ಯಾಕ್',
  'ಹೃದಯಾಘಾತ',
  'ಎದೆ ನೋವು',
  'ಉಸಿರಾಟ ನಿಲ್ಲುತ್ತಿದೆ',
  'ರಕ್ತಸ್ರಾವ',
  'ಪ್ರಜ್ಞೆ ತಪ್ಪಿದೆ',
];

/**
 * Checks if the spoken transcript contains life-threatening emergency terms.
 */
export const detectEmergencyKeywords = (text: string): boolean => {
  if (!text) return false;
  const lower = text.toLowerCase();
  return EMERGENCY_KEYWORDS.some((kw) => lower.includes(kw.toLowerCase()));
};

export interface EmergencyDispatchInfo {
  casualtyLocation: string;
  floorMarker: string;
  emergencyExtension: string;
  dispatchedToDoctor: boolean;
}

export const getEmergencyInstructions = (): EmergencyDispatchInfo => {
  return {
    casualtyLocation: 'Ground Floor, 50 meters straight ahead (Near Ambulance Bay)',
    floorMarker: 'BOLD RED LINE marked on the hospital floor outside this kiosk',
    emergencyExtension: '108',
    dispatchedToDoctor: true,
  };
};
