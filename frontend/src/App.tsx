import { useCallback, useEffect, useRef, useState } from 'react';
import { BookOpen, Plus, RotateCw } from 'lucide-react';
import { api, setToken } from './hooks/useApi';
import { useTelegram } from './hooks/useTelegram';
import { type AuthResponse, type Dashboard, type Tab, type Transaction, type User } from './types';
import { DashboardHeader } from './components/DashboardHeader';
import { TransactionList } from './components/TransactionList';
import { AddDebtModal } from './components/AddDebtModal';
import { RepayModal } from './components/RepayModal';
import { ReminderModal } from './components/ReminderModal';

type Dialog = { type: 'add' } | { type: 'repay'; item: Transaction; full: boolean } | { type: 'reminder'; item: Transaction } | null;

export default function App() {
  const telegram = useTelegram();
  const [user, setUser] = useState<User | null>(null);
  const [summary, setSummary] = useState<Dashboard | null>(null);
  const [items, setItems] = useState<Transaction[]>([]);
  const [tab, setTab] = useState<Tab>('all');
  const [dialog, setDialog] = useState<Dialog>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [attempt, setAttempt] = useState(0);
  const sequence = useRef(0);

  useEffect(() => {
    let alive = true;
    async function login() {
      setAuthLoading(true); setError('');
      try {
        setToken(null);
        if (!telegram.initData) throw new Error("Daftarni Telegram botidagi «Daftarni ochish» tugmasi orqali oching.");
        const result = await api<AuthResponse>('/auth/telegram', { method: 'POST', body: JSON.stringify({ init_data: telegram.initData }) });
        if (alive) { setToken(result.access_token); setUser(result.user); }
      } catch (failure) { if (alive) setError(failure instanceof Error ? failure.message : "Kirish amalga oshmadi"); }
      finally { if (alive) setAuthLoading(false); }
    }
    void login();
    return () => { alive = false; };
  }, [telegram.initData, attempt]);

  useEffect(() => {
    const expire = () => {
      sequence.current += 1;
      setUser(null); setSummary(null); setItems([]); setDialog(null);
      setError("Kirish muddati tugagan. Ilovani Telegram orqali qayta oching.");
    };
    window.addEventListener('qarzdaftar:unauthorized', expire);
    return () => window.removeEventListener('qarzdaftar:unauthorized', expire);
  }, []);

  const refresh = useCallback(async () => {
    if (!user) return;
    const request = ++sequence.current;
    setLoading(true); setError('');
    try {
      const [dashboard, rows] = await Promise.all([
        api<Dashboard>('/dashboard'), api<Transaction[]>('/transactions?tab=' + tab + '&limit=50'),
      ]);
      if (request === sequence.current) { setSummary(dashboard); setItems(rows); setHasMore(rows.length === 50); }
    } catch (failure) {
      if (request === sequence.current) setError(failure instanceof Error ? failure.message : "Ma'lumotlar olinmadi");
    } finally { if (request === sequence.current) setLoading(false); }
  }, [user, tab]);

  useEffect(() => { void refresh(); return () => { sequence.current += 1; }; }, [refresh]);
  useEffect(() => { if (!notice) return; const timer = window.setTimeout(() => setNotice(''), 7000); return () => window.clearTimeout(timer); }, [notice]);

  async function more() {
    if (loading) return;
    const request = ++sequence.current;
    setLoading(true);
    try {
      const rows = await api<Transaction[]>('/transactions?tab=' + tab + '&limit=50&offset=' + items.length);
      if (request === sequence.current) {
        setItems(previous => previous.concat(rows.filter(row => !previous.some(old => old.id === row.id))));
        setHasMore(rows.length === 50);
      }
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Ma'lumotlar olinmadi"); }
    finally { if (request === sequence.current) setLoading(false); }
  }
  function share(link: string) {
    telegram.openTelegramLink('https://t.me/share/url?url=' + encodeURIComponent(link) +
      '&text=' + encodeURIComponent("O'zaro hisob-kitobimizni tasdiqlashingizni so'rayman."));
  }
  if (authLoading || !user) return <main className="app-shell">
    <div className="entry-screen"><span className="brand-icon"><BookOpen size={26} /></span>
      <h1 className="text-3xl font-bold mt-5">Haq daftari</h1>
      <p className="text-slate-600 mt-4" role={authLoading ? 'status' : 'alert'}>{authLoading ? 'Telegram orqali kirilmoqda' : error}</p>
      {!authLoading && telegram.initData && <button className="primary mt-6" onClick={() => setAttempt(value => value + 1)}>Qayta urinish</button>}
      {!authLoading && !telegram.initData && import.meta.env.VITE_BOT_USERNAME &&
        <a className="primary mt-6" href={'https://t.me/' + import.meta.env.VITE_BOT_USERNAME}>Telegramda ochish</a>}
    </div>
  </main>;
  return <main className="app-shell">
    {summary ? <DashboardHeader data={summary} name={user.first_name} /> : <h1 className="text-2xl font-bold mb-6">Mening daftarim</h1>}
    {error && <div role="alert" className="error-box mb-5">{error}<button className="mt-2 flex gap-2 items-center underline" onClick={() => void refresh()}><RotateCw size={16} /> Qayta urinish</button></div>}
    {notice && <p role="status" className="notice-box mb-5">{notice}</p>}
    <TransactionList items={items} tab={tab} onTab={value => { if (value !== tab) { setItems([]); setTab(value); } }} loading={loading}
      onRepay={(item, full) => setDialog({ type: 'repay', item, full })}
      onRemind={item => setDialog({ type: 'reminder', item })} onShare={share}
      hasMore={hasMore} onMore={() => void more()} />
    <div className="floating-bar"><button className="primary" onClick={() => { telegram.haptic(); setDialog({ type: 'add' }); }}><Plus size={21} /> Qarz yozish</button></div>
    {dialog?.type === 'add' && <AddDebtModal onClose={() => setDialog(null)} onSaved={refresh} onShare={share} />}
    {dialog?.type === 'repay' && <RepayModal item={dialog.item} full={dialog.full} onClose={() => setDialog(null)} onSaved={refresh} />}
    {dialog?.type === 'reminder' && <ReminderModal item={dialog.item} onClose={() => setDialog(null)} onSaved={refresh} onNotice={setNotice} />}
  </main>;
}
