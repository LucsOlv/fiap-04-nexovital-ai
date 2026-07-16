interface VideoPlayerProps {
  src: string;
  title?: string;
}

export default function VideoPlayer({ src, title }: VideoPlayerProps) {
  return (
    <div>
      {title && <p className="mb-1 text-sm font-medium text-slate-900">{title}</p>}
      <video controls className="w-full max-w-md rounded-md border border-slate-200">
        <source src={src} />
        {title ?? "Vídeo"}
      </video>
    </div>
  );
}
