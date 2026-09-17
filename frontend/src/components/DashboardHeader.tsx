import { ArrowDownLeft, ArrowUpRight, BookOpen } from 'lucide-react';
import { type Dashboard, money } from '../types';

export function DashboardHeader({ data, name }: { data: Dashboard; name: string }) {
  return <header>
    <div className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-3"><span className="brand-icon"><BookOpen size={23} /></span>
        <span className="text-xl font-bold tracking-tight">Haq daftari</span></div>
      <span className="avatar" aria-label={name}>{name.slice(0, 1).toUpperCase()}</span>
    </div>
    <p className="text-sm text-slate-600 mb-1">Assalomu alaykum, {name}</p>
    <h1 className="text-3xl font-bold tracking-tight mb-6">Mening daftarim</h1>
    <div className="balance-grid">
      <section className="balance-card receivable">
        <ArrowDownLeft className="mb-5" size={24} /><h2>Menga berishlari kerak</h2>
        <p className="balance-amount">{money(data.total_receivable)} <small>so'm</small></p>
      </section>
      <section className="balance-card payable">
        <ArrowUpRight className="mb-5" size={24} /><h2>Men berishim kerak</h2>
        <p className="balance-amount">{money(data.total_payable)} <small>so'm</small></p>
      </section>
    </div>
    <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm mt-4 mb-8">
      <span><strong>{data.active_count}</strong> ta ochiq hisob</span>
      <span className={data.overdue_count ? 'text-rose-700' : 'text-slate-600'}><strong>{data.overdue_count}</strong> ta muddati o'tgan</span>
    </div>
  </header>;
}
