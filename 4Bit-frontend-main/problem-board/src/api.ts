const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the VoiceCare backend at ${API_BASE}. Start the backend and keep its terminal running.`);
    }
    throw error;
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch { /* response body was not JSON */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export type Conversation = {
  session_id: string;
  state: string;
  language: 'kn-IN' | 'en-IN';
  reply: string;
  summary?: string | null;
  draft?: { title?: string | null; description?: string | null; category?: string | null; location?: string | null; specific_location?: string | null } | null;
  missing_information?: string[];
  complaint?: {
    title: string;
    description: string;
    category: string | null;
    location: string;
    specific_location?: string | null;
  } | null;
};

export const startConversation = (language: 'kn-IN' | 'en-IN') =>
  request<{ session_id: string; state: string; reply: string }>('/api/conversation/start', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language }),
  });

export const sendMessage = (session_id: string, message: string) =>
  request<Conversation>('/api/conversation/message', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id, message }),
  });

export const confirmConversation = (session_id: string, confirmed: boolean) =>
  request<Conversation>('/api/conversation/confirm', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id, confirmed }),
  });

export const submitConversation = (sessionId: string) =>
  request<{ complaint_id: string; complaint_number: string; routed_category: string; routed_department: string; routing_assessment?: unknown }>(`/api/conversation/sessions/${encodeURIComponent(sessionId)}/submit`, { method: 'POST' });

export async function transcribeAudio(blob: Blob, language: 'kn-IN' | 'en-IN'): Promise<string> {
  const form = new FormData();
  form.append('file', blob, 'recording.webm');
  form.append('language_code', language);
  const result = await request<{ transcript: string }>('/api/voice/transcribe', { method: 'POST', body: form });
  return result.transcript;
}

export async function speak(text: string, language: 'kn-IN' | 'en-IN') {
  const response = await fetch(`${API_BASE}/api/voice/speak`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language_code: language }),
  });
  if (!response.ok) throw new Error('Voice response is temporarily unavailable.');
  const audio = new Audio(URL.createObjectURL(await response.blob()));
  audio.onended = () => URL.revokeObjectURL(audio.src);
  await audio.play();
}
