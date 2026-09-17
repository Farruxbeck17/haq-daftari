import { Bell, ChevronDown, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import { clsx } from 'clsx';
import { type Status, type Transaction, dateLabel, money, tashkentToday } from '../types';

const statuses: Record<Status, string> = {
  ACTIVE: 'Ochiq', PARTIALLY_PAID: "Qisman to'langan", SETTLED: 'Yopilgan',
  PENDING_CONFIRMATION: 'Tasdiq kutilmoqda', REJECTED: 'Rad etilgan',
};
export function TransactionCard({ item, onRepay, onRemind, onShare }: {
  item: Transaction; onRepay: (item: Transaction, full: boolean) => void;
  onRemind: (item: Transaction) => void; onShare: (link: string) => void;
}) {
  const given = item.type === 'GIVEN';
  const overdue = item.due_date && item.due_date < tashkentToday() && ['ACTIVE', 'PARTIALLY_PAID'].includes(item.status);
  return <article className="transaction-card">
    <div className="flex gap-3 items-start">
      <span className={clsx('direction-icon', given ? 'given' : 'taken')}>{given ? <ArrowDownLeft size={22} /> : <ArrowUpRight size={22} />}</span>
      <div className="min-w-0 flex-1"><h3 className="font-bold break-words">{item.counterparty_name}</h3>
        <p className="text-sm text-slate-600 mt-1">{given ? 'Haqdorman' : 'Qarzdorman'}</p></div>
      <span className={clsx('badge', item.status === 'SETTLED' && 'badge-settled')}>{statuses[item.status]}</span>
    </div>
    <div className="flex flex-wrap gap-3 items-end justify-between mt-5">
      <div><p className="text-sm text-slate-600">Qolgan summa</p>
        <p className="text-2xl font-bold mt-1 break-all">{money(item.remaining_amount)} <span className="text-sm font-normal">so'm</span></p></div>
      <div className="text-sm"><p className="text-slate-600">Jami {money(item.amount)} so'm</p>
        <p className={clsx('mt-1', overdue ? 'text-rose-700 font-medium' : 'text-slate-600')}>{dateLabel(item.due_date)}</p></div>
    </div>
    {item.note && <p className="text-sm text-slate-600 mt-4 whitespace-pre-wrap break-words">{item.note}</p>}
    {(item.can_repay || item.can_remind || item.confirmation_link) && <div className="card-actions">
      {item.can_repay && <><button onClick={() => onRepay(item, false)}>Qisman to'lash</button><button onClick={() => onRepay(item, true)}>Yopish</button></>}
      {item.can_remind && <button onClick={() => onRemind(item)}><Bell size={15} /> Eslatma</button>}
      {item.confirmation_link && <button onClick={() => onShare(item.confirmation_link!)}>Tasdiqlash uchun ulashish</button>}
    </div>}
    {item.repayments.length > 0 && <details className="mt-4 text-sm">
      <summary className="cursor-pointer flex items-center gap-2"><ChevronDown size={16} /> To'lovlar tarixi ({item.repayments.length})</summary>
      <ul className="mt-3 space-y-3">{item.repayments.map(payment => <li key={payment.id} className="border-t pt-3">
        <div className="flex justify-between gap-2"><strong>{money(payment.amount)} so'm</strong>
          <time dateTime={payment.paid_at}>{new Date(payment.paid_at).toLocaleDateString('uz-UZ', { timeZone: 'Asia/Tashkent' })}</time></div>
        {payment.note && <p className="mt-1 break-words">{payment.note}</p>}
      </li>)}</ul>
    </details>}
  </article>;
}
