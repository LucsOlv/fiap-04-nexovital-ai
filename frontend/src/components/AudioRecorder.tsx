import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { encodeWav } from "@/lib/wav";

interface AudioRecorderProps {
  onRecorded: (file: File | null) => void;
}

const MAX_AUDIO_MS = 2 * 60 * 1000;

export default function AudioRecorder({ onRecorded }: AudioRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [error, setError] = useState<string>();
  const recorderRef = useRef<MediaRecorder>();
  const timeoutRef = useRef<number>();
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function start() {
    setError(undefined);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Gravação não suportada neste navegador. Envie um arquivo.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        await finalize(new Blob(chunksRef.current));
      };
      recorderRef.current = recorder;
      recorder.start();
      timeoutRef.current = window.setTimeout(() => {
        if (recorder.state === "recording") recorder.stop();
      }, MAX_AUDIO_MS);
      setRecording(true);
      setError("Gravação limitada a 2 minutos.");
    } catch {
      setError("Não foi possível acessar o microfone. Verifique as permissões.");
    }
  }

  async function finalize(recorded: Blob) {
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    try {
      const AudioCtx =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const context = new AudioCtx();
      const decoded = await context.decodeAudioData(await recorded.arrayBuffer());
      await context.close();
      const wav = encodeWav(decoded);
      const file = new File([wav], "gravacao.wav", { type: "audio/wav" });
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(wav));
      setError(undefined);
      onRecorded(file);
    } catch {
      setError("Falha ao processar o áudio gravado.");
    }
  }

  function stop() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setError("Áudio excede limite de 10 MB.");
      event.target.value = "";
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
    setError(undefined);
    onRecorded(file);
  }

  function reset() {
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(undefined);
    setError(undefined);
    onRecorded(null);
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {!recording ? (
          <Button type="button" onClick={start}>
            {previewUrl ? "Gravar novamente" : "Gravar áudio"}
          </Button>
        ) : (
          <Button type="button" onClick={stop}>
            Parar gravação
          </Button>
        )}
        <label className="inline-flex cursor-pointer items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Enviar arquivo
          <input
            type="file"
            accept="audio/wav,audio/mp3,audio/mpeg,audio/m4a,audio/x-m4a,audio/webm"
            className="hidden"
            onChange={handleUpload}
          />
        </label>
        {previewUrl && !recording && (
          <Button type="button" variant="ghost" className="text-slate-600" onClick={reset}>
            Remover
          </Button>
        )}
      </div>
      {recording && (
        <p role="status" className="text-sm text-red-600">
          Gravando áudio. Limite de 2 minutos.
        </p>
      )}
      {previewUrl && !recording && <audio controls src={previewUrl} className="w-full" />}
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
