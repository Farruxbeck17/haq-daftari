import { useEffect, useState } from 'react';
import { init, retrieveRawInitData, miniApp, viewport, hapticFeedback, openTelegramLink as openLink } from '@telegram-apps/sdk-react';

let initialized = false;

function readInitData() {
  try { return retrieveRawInitData() || ''; } catch { return ''; }
}

export function useTelegram() {
  const [initData] = useState(readInitData);
  useEffect(() => {
    if (!initData) return;
    try {
      if (!initialized) { init(); initialized = true; }
      if (miniApp.mountSync.isAvailable()) miniApp.mountSync();
      if (miniApp.ready.isAvailable()) miniApp.ready();
      if (viewport.expand.isAvailable()) viewport.expand();
    } catch { /* Eski Telegram talqinida asosiy hisob-kitob ishlashda davom etadi. */ }
  }, [initData]);
  let user: { id: number; first_name: string } | null = null;
  try { user = JSON.parse(new URLSearchParams(initData).get('user') || 'null'); } catch { user = null; }
  return {
    initData,
    user,
    haptic() {
      if (hapticFeedback.impactOccurred.isAvailable()) hapticFeedback.impactOccurred('light');
    },
    openTelegramLink(url: string) {
      const parsed = new URL(url);
      if (parsed.protocol !== 'https:' || parsed.hostname !== 't.me') return;
      if (openLink.isAvailable()) openLink(url);
      else window.open(url, '_blank', 'noopener,noreferrer');
    },
  };
}
