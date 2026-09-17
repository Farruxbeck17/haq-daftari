import { BookOpen } from 'lucide-react';
import { clsx } from 'clsx';
import { type Tab, type Transaction } from '../types';
import { TransactionCard } from './TransactionCard';
const tabs: { value: Tab; label: string }[] = [
  { value: 'all', label: 'Barchasi' }, { value: 'overdue', label: "Muddati o'tgan" },
  { value: 'upcoming', label: 'Kutilayotgan' }, { value: 'settled', label: 'Yopilgan' },
];
export function TransactionList({ items, tab, onTab, loading, onRepay, onRemind, onShare, hasMore, onMore }: {
  items: Transaction[]; tab: Tab; onTab: (tab: Tab) => void; loading: boolean;
  onRepay: (item: Transaction, full: boolean) => void; onRemind: (item: Transaction) => void;
  onShare: (link: string) => void; hasMore: boolean; onMore: () => void;
}) {
  return <section aria-label="Qarz yozuvlari">
    <nav className="tabs" aria-label="Qarzlarni saralash">{tabs.map(entry =>
      <button key={entry.value} className={clsx(tab === entry.value && 'selected')} aria-current={tab === entry.value ? 'page' : undefined}
        onClick={() => onTab(entry.value)}>{entry.label}</button>)}</nav>
    <div aria-busy={loading}>
      {items.length === 0 && !loading && <div className="empty-state"><BookOpen size={38} />
        <h2 className="font-bold text-lg mt-4">Hozircha yozuv yo'q</h2>
        <p className="text-slate-600 mt-2">{tab === 'all' ? "Birinchi hisob-kitobingizni «Qarz yozish» orqali kiriting." : "Bu bo'limda qarz yozuvlari topilmadi."}</p>
      </div>}
      <div className="space-y-4">{items.map(item => <TransactionCard key={item.id} item={item}
        onRepay={onRepay} onRemind={onRemind} onShare={onShare} />)}</div>
      {loading && <p role="status" className="text-center p-6">Yuklanmoqda</p>}
      {hasMore && !loading && <button className="secondary w-full mt-4" onClick={onMore}>Yana ko'rsatish</button>}
    </div>
  </section>;
}
