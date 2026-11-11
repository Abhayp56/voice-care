/**
 * Frontend TTS is disabled.
 * Audio and voice connections are now handled exclusively by the backend.
 */
export interface SpeakOptions {
  fallbackTimeoutMs?: number;
  onStart?: () => void;
  onEnd?: () => void;
}

export const speakPrompt = async (
  _text?: string,
  _lang?: 'kn' | 'en',
  options?: SpeakOptions
): Promise<void> => {
  options?.onStart?.();
  options?.onEnd?.();
  return Promise.resolve();
};

export default speakPrompt;
