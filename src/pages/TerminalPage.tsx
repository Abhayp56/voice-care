import React, { useEffect, useRef, useState } from 'react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
type Language = 'kn-IN' | 'en-IN';
type Conversation = {
  session_id: string;
  state: string;
  language: Language;
  reply: string;
  summary?: string | null;
  complaint?: { title: string; description: string; category: string; location: string } | null;
};

async function jsonRequest<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data as T;
}

export const TerminalPage: React.FC = () => {
  const [language, setLanguage] = useState<Language>('kn-IN');
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [message, setMessage] = useState('');
  const [transcript, setTranscript] = useState('');
  const [complaintNumber, setComplaintNumber] = useState('');
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => () => {
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const speak = async (text: string, selectedLanguage = language) => {
    try {
      const response = await fetch(`${API_BASE}/api/voice/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language_code: selectedLanguage }),
      });
      if (!response.ok) return;
      const url = URL.createObjectURL(await response.blob());
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch {
      // Text remains available if the browser blocks audio playback.
    }
  };

  const start = async (selectedLanguage: Language) => {
    setBusy(true);
    setError('');
    setLanguage(selectedLanguage);
    try {
      const result = await jsonRequest<Conversation>('/api/conversation/start', { language: selectedLanguage });
      setConversation(result);
      await speak(result.reply, selectedLanguage);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start a conversation.');
    } finally {
      setBusy(false);
    }
  };

  const sendText = async (text: string) => {
    if (!conversation || !text.trim()) return;
    setBusy(true);
    setError('');
    setTranscript(text);
    try {
      const result = await jsonRequest<Conversation>('/api/conversation/message', {
        session_id: conversation.session_id,
        message: text.trim(),
      });
      setConversation(result);
      await speak(result.reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send that message.');
    } finally {
      setBusy(false);
    }
  };

  const startRecording = async () => {
    setError('');
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('This browser does not support microphone recording. You can type your message instead.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        const mime = recorder.mimeType || 'audio/webm';
        const extension = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm';
        const audio = new Blob(chunksRef.current, { type: mime });
        if (!audio.size) return;
        setBusy(true);
        setError('');
        try {
          const form = new FormData();
          form.append('file', audio, `patient-recording.${extension}`);
          form.append('language_code', language);
          const response = await fetch(`${API_BASE}/api/voice/transcribe`, { method: 'POST', body: form });
          const result = await response.json();
          if (!response.ok) throw new Error(result.detail || `Transcription failed (${response.status})`);
          const text = String(result.transcript || '').trim();
          if (!text) throw new Error('No speech was recognized. Please try again or type your message.');
          setTranscript(text);
          await sendText(text);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Transcription failed.');
        } finally {
          setBusy(false);
        }
      };
      recorder.start();
      setRecording(true);
    } catch {
      setError('Microphone access was not granted. You can type your message instead.');
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state === 'inactive') return;
    setRecording(false);
    recorderRef.current.stop();
  };

  const confirm = async (confirmed: boolean) => {
    if (!conversation) return;
    setBusy(true);
    setError('');
    try {
      const result = await jsonRequest<Conversation>('/api/conversation/confirm', {
        session_id: conversation.session_id,
        confirmed,
      });
      setConversation(result);
      await speak(result.reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm the complaint.');
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!conversation) return;
    setBusy(true);
    setError('');
    try {
      const result = await jsonRequest<{ complaint_number: string }>(`/api/conversation/sessions/${conversation.session_id}/submit`, {});
      setComplaintNumber(result.complaint_number);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The complaint was not submitted.');
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setConversation(null);
    setMessage('');
    setTranscript('');
    setComplaintNumber('');
    setError('');
  };

  if (complaintNumber) return (
    <main className="mx-auto flex min-h-[80vh] max-w-3xl flex-col items-center justify-center gap-6 p-6 text-center">
      <div className="text-6xl" aria-hidden="true">✓</div>
      <h1 className="text-3xl font-bold text-emerald-900">Complaint submitted</h1>
      <p>Your reference number is</p>
      <p className="rounded-xl bg-emerald-950 px-8 py-4 font-mono text-3xl font-bold text-white">{complaintNumber}</p>
      <p>Save this number to check your complaint status.</p>
      <button className="rounded-lg bg-emerald-900 px-6 py-3 font-semibold text-white" onClick={reset}>Start another complaint</button>
    </main>
  );

  if (!conversation) return (
    <main className="mx-auto flex min-h-[80vh] max-w-3xl flex-col items-center justify-center gap-8 p-6 text-center">
      <div className="text-6xl" aria-hidden="true">♥</div>
      <h1 className="text-3xl font-bold text-emerald-950">4BIT VoiceCare</h1>
      <p className="max-w-xl text-lg">Tell us about a hospital service problem. You can speak or type, review the details, and confirm before submission.</p>
      <div className="flex flex-wrap justify-center gap-4">
        <button disabled={busy} onClick={() => void start('kn-IN')} className="rounded-xl bg-emerald-900 px-8 py-4 text-lg font-bold text-white disabled:opacity-50">ಕನ್ನಡದಲ್ಲಿ ಮುಂದುವರಿಸಿ</button>
        <button disabled={busy} onClick={() => void start('en-IN')} className="rounded-xl border-2 border-emerald-900 px-8 py-4 text-lg font-bold text-emerald-950 disabled:opacity-50">Continue in English</button>
      </div>
      {busy && <p role="status">Connecting…</p>}
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
    </main>
  );

  const emergency = conversation.state === 'EMERGENCY_REDIRECTED';
  const awaitingConfirmation = conversation.state === 'AWAITING_CONFIRMATION';
  const confirmed = conversation.state === 'CONFIRMED';

  return (
    <main className="mx-auto flex min-h-[80vh] max-w-3xl flex-col gap-6 p-4 pt-24 sm:p-8">
      <header className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-emerald-950">Patient voice terminal</h1>
        <button onClick={reset} className="rounded border px-3 py-2 text-sm">End conversation</button>
      </header>

      {emergency ? (
        <section role="alert" className="space-y-4 rounded-2xl border-4 border-red-800 bg-red-50 p-6 text-red-950">
          <h2 className="text-2xl font-black">Please get emergency help now</h2>
          <p>{conversation.reply}</p>
          <p>Go to the hospital emergency or casualty desk, or ask someone nearby to contact hospital staff. This screen does not dispatch an alert.</p>
        </section>
      ) : (
        <>
          <section aria-live="polite" className="space-y-3 rounded-2xl bg-white p-5 shadow">
            <p className="font-semibold text-emerald-950">VoiceCare</p>
            <p>{conversation.reply}</p>
            {transcript && <><p className="text-sm font-semibold text-slate-600">Recognized speech</p><p className="rounded bg-slate-50 p-3">{transcript}</p></>}
            {conversation.summary && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4"><p className="font-bold">Please review this summary</p><p>{conversation.summary}</p></div>}
          </section>

          {!confirmed && !awaitingConfirmation && (
            <section className="space-y-4 rounded-2xl bg-white p-5 shadow">
              <div className="flex flex-wrap gap-3">
                {!recording ? <button disabled={busy} onClick={() => void startRecording()} className="rounded-lg bg-emerald-900 px-5 py-3 font-semibold text-white disabled:opacity-50">Start microphone</button> : <button onClick={stopRecording} className="rounded-lg bg-red-700 px-5 py-3 font-semibold text-white">Stop recording</button>}
                {recording && <span role="status" className="self-center text-red-700">Recording…</span>}
              </div>
              <form onSubmit={(event) => { event.preventDefault(); const text = message; setMessage(''); void sendText(text); }} className="flex flex-col gap-3 sm:flex-row">
                <label className="sr-only" htmlFor="patient-message">Type your message</label>
                <input id="patient-message" value={message} onChange={(event) => setMessage(event.target.value)} maxLength={4000} className="min-w-0 flex-1 rounded-lg border p-3" placeholder="Or type what happened" />
                <button disabled={busy || !message.trim()} className="rounded-lg border px-5 py-3 font-semibold disabled:opacity-50">Send</button>
              </form>
            </section>
          )}

          {awaitingConfirmation && <div className="flex flex-wrap gap-3"><button disabled={busy} onClick={() => void confirm(true)} className="rounded-lg bg-emerald-900 px-6 py-3 font-bold text-white">Confirm details</button><button disabled={busy} onClick={() => void confirm(false)} className="rounded-lg border px-6 py-3 font-semibold">Correct details</button></div>}
          {confirmed && <button disabled={busy} onClick={() => void submit()} className="rounded-lg bg-emerald-900 px-6 py-3 font-bold text-white disabled:opacity-50">Submit confirmed complaint</button>}
        </>
      )}

      {busy && <p role="status">Working…</p>}
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
    </main>
  );
};

export default TerminalPage;
