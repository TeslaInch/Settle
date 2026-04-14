"use client";

import { useEffect, useState } from "react";
import { Share, X } from "lucide-react";

const DISMISS_KEY = "settle_install_dismissed_at";
const DISMISS_DURATION_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

type Platform = "android" | "ios" | null;

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export default function InstallPrompt() {
  const [platform, setPlatform] = useState<Platform>(null);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [showIOSSteps, setShowIOSSteps] = useState(false);

  useEffect(() => {
    // Don't show if already running as installed PWA
    if (window.matchMedia("(display-mode: standalone)").matches) return;

    // Don't show if dismissed within 7 days
    const dismissedAt = localStorage.getItem(DISMISS_KEY);
    if (dismissedAt && Date.now() - Number(dismissedAt) < DISMISS_DURATION_MS) return;

    // Don't show unless user has created at least one agreement
    const hasAgreement = localStorage.getItem("settle_has_agreement");
    if (!hasAgreement) return;

    const ua = navigator.userAgent;
    const isIOS = /iphone|ipad|ipod/i.test(ua) && !(window as unknown as { MSStream?: unknown }).MSStream;
    const isAndroid = /android/i.test(ua);

    if (isIOS) {
      setPlatform("ios");
      setVisible(true);
    } else if (isAndroid) {
      // Android: wait for beforeinstallprompt
      const handler = (e: Event) => {
        e.preventDefault();
        setDeferredPrompt(e as BeforeInstallPromptEvent);
        setPlatform("android");
        setVisible(true);
      };
      window.addEventListener("beforeinstallprompt", handler);
      return () => window.removeEventListener("beforeinstallprompt", handler);
    }
  }, []);

  const handleInstall = async () => {
    if (platform === "android" && deferredPrompt) {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === "accepted") {
        setVisible(false);
      }
      setDeferredPrompt(null);
    } else if (platform === "ios") {
      setShowIOSSteps(true);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="banner"
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-100 shadow-lg px-4 py-4 max-w-[480px] mx-auto"
    >
      {!showIOSSteps ? (
        <div className="flex items-center gap-3">
          {/* App icon */}
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#1B4332]">
            <span className="text-white font-bold text-lg">S</span>
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900">Install Settle for quick access</p>
            <p className="text-xs text-gray-400 mt-0.5">Works offline too</p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleInstall}
              className="rounded-full bg-green-600 px-4 py-1.5 text-xs font-semibold text-white"
            >
              Install
            </button>
            <button
              onClick={handleDismiss}
              aria-label="Dismiss install prompt"
              className="p-1 text-gray-400"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      ) : (
        /* iOS manual instructions */
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-gray-900">Add to Home Screen</p>
            <button onClick={handleDismiss} aria-label="Close" className="p-1 text-gray-400">
              <X size={18} />
            </button>
          </div>
          <ol className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="shrink-0 font-semibold text-green-600">1.</span>
              <span>
                Tap the{" "}
                <Share size={14} className="inline mb-0.5 text-blue-500" />{" "}
                <strong>Share</strong> button at the bottom of Safari
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="shrink-0 font-semibold text-green-600">2.</span>
              <span>Scroll down and tap <strong>Add to Home Screen</strong></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="shrink-0 font-semibold text-green-600">3.</span>
              <span>Tap <strong>Add</strong> in the top right</span>
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
