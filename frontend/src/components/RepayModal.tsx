import { useState, type FormEvent } from 'react';
import { ApiError, useApi } from '../hooks/useApi';
import { type Transaction, money } from '../types';
import { Modal } from './Modal';

interface PendingPayment { amount: string; note: string; idempotency_key: string }
function readPending(key: string): PendingPayment | null {
  try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch { return null; }
}
export function RepayModal({ item, full, onClose, onSaved }: {
  item: Transaction; full: boolean; onClose: () => void; onSaved: () => Promise<void>;
}) {
  const api = useApi();
  const storageKey = 'qarzdaftar_payment_' + item.id;
  const [pending, setPending] = useState<PendingPayment | null>(() => readPending(storageKey));
  const [amount, setAmount] = useState(pending?.amount || (full ? item.remaining_amount : ''));
  const [note, setNote] = useState(pending?.note || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError('');
    const payload = pending || { amount, note, idempotency_key: crypto.randomUUID() };
    setPending(payload); sessionStorage.setItem(storageKey, JSON.stringify(payload));
    try {
      await api<Transaction>('/transactions/' + item.id + '/repay', { method: 'POST', body: JSON.stringify(payload) });
      sessionStorage.removeItem(storageKey);
      await onSaved(); onClose();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "To'lov saqlanmadi");
      if (failure instanceof ApiError && failure.status >= 400 && failure.status < 500) {
        sessionStorage.removeItem(storageKey); setPending(null);
      }
    } finally { setBusy(false); }
  }
  return <Modal title={full ? 'Qarzni yopish' : "To'lovni qayd etish"} onClose={onClose} busy={busy}>
    <form onSubmit={submit} className="space-y-5">
      <p><strong>{item.counterparty_name}</strong> bilan hisob-kitob</p>
      <p className="text-slate-600">Qolgan summa: <strong className="text-ink">{money(item.remaining_amount)} so'm</strong></p>
      <p className="text-sm text-slate-600">Faqat amalda olingan yoki berilgan pulni qayd eting. Bu amal pul o'tkazmaydi.</p>
      <label>To'langan summa, so'm<input required autoFocus type="number" inputMode="decimal" min="0.01" max={item.remaining_amount} step="0.01"
        value={amount} readOnly={full || pending !== null} disabled={busy} onChange={event => setAmount(event.target.value)} /></label>
      <label>Izoh <span className="optional">ixtiyoriy</span><textarea maxLength={1000} rows={3} value={note} readOnly={pending !== null} disabled={busy} onChange={event => setNote(event.target.value)} /></label>
      {pending && !busy && <p className="text-sm text-slate-600">Oldingi so'rov javobi tekshiriladi. Qayta yuborish bir to'lovni ikki marta yozmaydi.</p>}
      {error && <p role="alert" className="error-box">{error}</p>}
      <button className="primary w-full" disabled={busy}>{busy ? 'Saqlanmoqda' : pending ? "So'rovni qayta tekshirish" : full ? 'To‘liq to‘lovni tasdiqlash' : "To'lovni saqlash"}</button>
    </form>
  </Modal>;
}
