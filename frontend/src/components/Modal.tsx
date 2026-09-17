import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

export function Modal({ title, onClose, busy = false, children }: {
  title: string; onClose: () => void; busy?: boolean; children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement as HTMLElement | null;
    element?.showModal();
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { element?.close(); document.body.style.overflow = oldOverflow; previous?.focus(); };
  }, []);
  return <dialog ref={dialog} className="sheet" aria-labelledby="dialog-title"
    onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}
    onClick={event => {
      if (!busy && event.target === dialog.current) {
        const rect = dialog.current.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) onClose();
      }
    }}>
    <div className="sheet-handle" />
    <header className="flex items-center justify-between gap-4 mb-6">
      <h2 id="dialog-title" className="text-xl font-bold">{title}</h2>
      <button type="button" className="icon-button" aria-label="Yopish" onClick={onClose} disabled={busy}><X size={22} /></button>
    </header>
    {children}
  </dialog>;
}
