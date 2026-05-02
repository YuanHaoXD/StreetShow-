"use client";

import { useEffect, useRef, useState } from "react";

type ImageUploaderProps = {
  label: string;
  hint?: string;
  onFile?: (file: File | null) => void;
};

export default function ImageUploader({
  label,
  hint,
  onFile,
}: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleFile = (file: File | null) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    if (file) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
    onFile?.(file);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    handleFile(file);
  };

  const clearFile = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (inputRef.current) {
      inputRef.current.value = "";
    }
    handleFile(null);
  };

  return (
    <div
      className={[
        "group relative flex h-72 w-full items-center justify-center rounded-2xl",
        "border border-neonPurple/50 bg-white/5 backdrop-blur-md",
        "neon-frame",
        "transition-shadow duration-300",
        dragActive ? "shadow-[0_0_30px_rgba(176,38,255,0.6)]" : "shadow-none",
      ].join(" ")}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="absolute inset-0 cursor-pointer opacity-0"
        onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
      />
      {previewUrl ? (
        <div className="scanline h-full w-full rounded-2xl bg-black/40">
          <button
            type="button"
            onClick={clearFile}
            className="absolute right-3 top-3 rounded-full border border-white/40 bg-black/60 px-2 py-1 text-xs text-white hover:border-white"
          >
            -
          </button>
          <img
            src={previewUrl}
            alt={label}
            className="h-full w-full rounded-2xl object-contain"
          />
        </div>
      ) : (
        <div className="text-center">
          <p className="text-lg font-semibold text-neonPurple">{label}</p>
          <p className="mt-2 text-sm text-white/70">
            {hint ?? "拖拽或点击上传"}
          </p>
        </div>
      )}
    </div>
  );
}
