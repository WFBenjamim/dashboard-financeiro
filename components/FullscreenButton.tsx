"use client";

import { Maximize2, Minimize2 } from "lucide-react";
import { useEffect, useState } from "react";

export function FullscreenButton() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    setIsSupported(
      typeof document.documentElement.requestFullscreen === "function"
      && typeof document.exitFullscreen === "function"
    );

    function handleFullscreenChange() {
      setIsFullscreen(Boolean(document.fullscreenElement));
    }

    handleFullscreenChange();
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  if (!isSupported) return null;

  const label = isFullscreen ? "Sair da tela cheia" : "Ativar tela cheia";
  const Icon = isFullscreen ? Minimize2 : Maximize2;

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await document.documentElement.requestFullscreen();
      }
    } catch {
      // Browsers may reject fullscreen when it is blocked by user settings.
    }
  }

  return (
    <button
      className="gd-fullscreen-button"
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={isFullscreen}
      onClick={(event) => {
        event.stopPropagation();
        void toggleFullscreen();
      }}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <Icon aria-hidden="true" size={18} strokeWidth={2} />
    </button>
  );
}
