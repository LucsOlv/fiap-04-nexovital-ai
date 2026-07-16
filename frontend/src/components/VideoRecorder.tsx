import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

interface VideoRecorderProps {
  onRecorded: (file: File | null) => void;
}

const MAX_VIDEO_MS = 30 * 1000;

export default function VideoRecorder({ onRecorded }: VideoRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [error, setError] = useState<string>();
  const liveRef = useRef<HTMLVideoElement>(null);
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
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (liveRef.current) {
        liveRef.current.srcObject = stream;
        await liveRef.current.play().catch(() => undefined);
      }
      const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
        stream.getTracks().forEach((track) => track.stop());
        if (liveRef.current) liveRef.current.srcObject = null;
        const blob = new Blob(chunksRef.current, { type: "video/webm" });
        const file = new File([blob], "gravacao.webm", { type: "video/webm" });
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setPreviewUrl(URL.createObjectURL(blob));
        setError(undefined);
        onRecorded(file);
      };
      recorderRef.current = recorder;
      recorder.start();
      timeoutRef.current = window.setTimeout(() => {
        if (recorder.state === "recording") recorder.stop();
      }, MAX_VIDEO_MS);
      setRecording(true);
      setError("Gravação limitada a 30 segundos.");
    } catch {
      setError("Não foi possível acessar a câmera. Verifique as permissões.");
    }
  }

  function stop() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      setError("Vídeo excede limite de 25 MB.");
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
      <video
        ref={liveRef}
        muted
        playsInline
        className={recording ? "w-full rounded-md bg-black" : "hidden"}
      />
      {previewUrl && !recording && (
        <video controls src={previewUrl} className="w-full rounded-md bg-black" />
      )}
      {recording && (
        <p role="status" className="text-sm text-red-600">
          Gravando vídeo. Limite de 30 segundos.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        {!recording ? (
          <Button type="button" onClick={start}>
            {previewUrl ? "Gravar novamente" : "Gravar vídeo"}
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
            accept="video/mp4,video/webm,video/quicktime"
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
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      {!previewUrl && !recording && (
        <p className="text-xs text-slate-500">Sem vídeo selecionado.</p>
      )}
    </div>
  );
}
