import { useState, type FormEvent } from 'react';
import { Check, Send } from 'lucide-react';
import { clsx } from 'clsx';
import { useApi } from '../hooks/useApi';
import { type DebtType, type Transaction, money } from '../types';
import { Modal } from './Modal';

export function AddDebtModal({ onClose, onSaved, onShare }: {
  onClose: () => void; onSaved: () => Promise<void>; onShare: (link: string) => void;
}) {
  const api = useApi();
  const [type, setType] = useState<DebtType>('GIVEN');
  const [amount, setAmount] = useState('');
  const [share, setShare] = useState(false);
  const [saved, setSaved] = useState<Transaction | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const values = new FormData(event.currentTarget);
    setBusy(true); setError('');
    try {
      const item = await api<Transaction>('/transactions', { method: 'POST', body: JSON.stringify({
        type, amount, counterparty_name: String(values.get('name')).trim(),
        counterparty_phone: values.get('phone') || null, due_date: values.get('due') || null,
        note: values.get('note') || null, share_with_telegram: share, currency: 'UZS',
      }) });
      setSaved(item);
      await onSaved();
      if (!item.confirmation_link) onClose();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Saqlab bo'lmadi"); }
    finally { setBusy(false); }
  }
  return <Modal title={saved ? 'Qarz yozuvi saqlandi' : 'Qarz yozish'} onClose={onClose} busy={busy}>
    {saved ? <div className="space-y-5">
      <div className="success-icon"><Check size={28} /></div>
      <p>Do'stingiz tasdiqlagach, bu yozuv ikkalangizning daftaringizda ko'rinadi.</p>
      {saved.confirmation_link && <><label>Tasdiqlash havolasi<input readOnly value={saved.confirmation_link} onFocus={event => event.currentTarget.select()} /></label>
        <button className="primary w-full" onClick={() => onShare(saved.confirmation_link!)}><Send size={18} /> Telegram orqali ulashish</button></>}
      <button className="secondary w-full" onClick={onClose}>Tayyor</button>
    </div> : <form onSubmit={submit} className="space-y-5">
      <fieldset disabled={busy} className="space-y-5">
        <div className="segmented" aria-label="Qarz turi">
          <button type="button" aria-pressed={type === 'GIVEN'} className={clsx(type === 'GIVEN' && 'selected')} onClick={() => setType('GIVEN')}>Men berdim</button>
          <button type="button" aria-pressed={type === 'TAKEN'} className={clsx(type === 'TAKEN' && 'selected')} onClick={() => setType('TAKEN')}>Men oldim</button>
        </div>
        <label>Summa, so'm<input autoFocus required type="number" inputMode="decimal" min="0.01" max="999999999999.99" step="0.01"
          value={amount} onChange={event => setAmount(event.target.value)} /></label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">{[50000, 100000, 500000, 1000000].map(value =>
          <button key={value} type="button" className="amount-chip" onClick={() => setAmount(String(Math.min(999999999999.99, Number(amount || 0) + value)))}>+{money(value)}</button>)}</div>
        <label>Ism<input name="name" required maxLength={255} autoComplete="name" /></label>
        <label>Telefon raqami <span className="optional">ixtiyoriy</span><input name="phone" type="tel" pattern="\+998[0-9]{9}" title="+998 bilan boshlanuvchi 12 ta raqam" autoComplete="tel" />
          <small>Masalan: +998901234567</small></label>
        <label>Qaytarish muddati <span className="optional">ixtiyoriy</span><input name="due" type="date" /></label>
        <label>Izoh <span className="optional">ixtiyoriy</span><textarea name="note" maxLength={1000} rows={3} /></label>
        <label className="checkbox-row"><input type="checkbox" checked={share} onChange={event => setShare(event.target.checked)} />
          <span>Do'stga tasdiqlash uchun ulashish</span></label>
        {share && <p className="text-sm text-slate-600">Havolani faqat hisob-kitobdagi do'stingizga yuboring. Havola orqali kirgan birinchi kishi yozuvni tasdiqlashi yoki rad etishi mumkin.</p>}
      </fieldset>
      {error && <p role="alert" className="error-box">{error}</p>}
      <button className="primary w-full" disabled={busy} type="submit">{busy ? 'Saqlanmoqda' : 'Qarzni saqlash'}</button>
    </form>}
  </Modal>;
}
