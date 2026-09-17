import { useState, type FormEvent } from 'react';
import { useApi } from '../hooks/useApi';
import { type Transaction, money } from '../types';
import { Modal } from './Modal';

export function ReminderModal({ item, onClose, onSaved, onNotice }: {
  item: Transaction; onClose: () => void; onSaved: () => Promise<void>; onNotice: (message: string) => void;
}) {
  const api = useApi();
  const [tone, setTone] = useState<'friendly' | 'formal'>('friendly');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const remaining = item.last_reminder_sent_at ? Math.max(0, 86400000 - (Date.now() - Date.parse(item.last_reminder_sent_at))) : 0;
  async function submit(event: FormEvent) {
    event.preventDefault(); if (busy) return;
    setBusy(true); setError('');
    try {
      const result = await api<{ message: string }>('/transactions/' + item.id + '/send-reminder', { method: 'POST', body: JSON.stringify({ tone }) });
      onNotice(result.message); await onSaved(); onClose();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Eslatma yuborilmadi"); }
    finally { setBusy(false); }
  }
  return <Modal title="Muloyim eslatma" onClose={onClose} busy={busy}>
    <form onSubmit={submit} className="space-y-5">
      <p><strong>{item.counterparty_name}</strong> uchun eslatma</p>
      <fieldset disabled={busy}><legend className="font-medium mb-3">Muloqot ohangi</legend>
        <div className="grid grid-cols-2 gap-3">
          <label className="radio-option"><input type="radio" name="tone" checked={tone === 'friendly'} onChange={() => setTone('friendly')} /> Do'stona</label>
          <label className="radio-option"><input type="radio" name="tone" checked={tone === 'formal'} onChange={() => setTone('formal')} /> Rasmiy</label>
        </div>
      </fieldset>
      <blockquote className="reminder-preview">{tone === 'friendly'
        ? "Assalomu alaykum! O'zaro hisob-kitobni muloyim eslatib qo'ymoqchimiz."
        : "Hurmatli foydalanuvchi, o'zaro hisob-kitob bo'yicha eslatma."}
        <p className="mt-3">Qolgan summa: {money(item.remaining_amount)} so'm.</p>
        <p className="mt-3">{tone === 'friendly' ? "Qulay paytda hisob-kitob qilsangiz, xursand bo'lamiz. Rahmat!" : "Imkoningiz bo'lganda hisob-kitobni amalga oshirishingizni so'raymiz. Rahmat."}</p>
      </blockquote>
      <p className="text-sm text-slate-600">Eslatma har 24 soatda bir marta yuboriladi. SMS yuborilsa, SMS hisobingizdan bitta xabar yechiladi.</p>
      {remaining > 0 && <p role="status" className="error-box">Yana {Math.ceil(remaining / 3600000)} soatdan keyin yuborish mumkin.</p>}
      {error && <p role="alert" className="error-box">{error}</p>}
      <button className="primary w-full" disabled={busy || remaining > 0}>{busy ? 'Yuborilmoqda' : 'Eslatmani yuborish'}</button>
    </form>
  </Modal>;
}
