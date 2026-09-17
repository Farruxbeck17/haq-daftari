export type DebtType = 'GIVEN' | 'TAKEN';
export type Status = 'PENDING_CONFIRMATION' | 'ACTIVE' | 'PARTIALLY_PAID' | 'SETTLED' | 'REJECTED';
export type Tab = 'all' | 'overdue' | 'upcoming' | 'settled';
export interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name: string | null;
  username: string | null;
  phone_number: string | null;
  preferred_currency: string;
  sms_balance: number;
}
export interface Repayment { id: string; amount: string; paid_at: string; note: string | null }
export interface Transaction {
  id: string;
  creator_id: number;
  counterparty_id: number | null;
  counterparty_name: string;
  counterparty_phone: string | null;
  type: DebtType;
  amount: string;
  remaining_amount: string;
  currency: string;
  due_date: string | null;
  status: Status;
  note: string | null;
  last_reminder_sent_at: string | null;
  created_at: string;
  updated_at: string;
  confirmation_link: string | null;
  can_repay: boolean;
  can_remind: boolean;
  repayments: Repayment[];
}
export interface Dashboard {
  total_receivable: number;
  total_payable: number;
  active_count: number;
  overdue_count: number;
}
export interface AuthResponse { access_token: string; token_type: string; user: User }
export const money = (value: string | number) => new Intl.NumberFormat('uz-UZ', {
  maximumFractionDigits: 2,
}).format(Number(value));
export const dateLabel = (value: string | null) => value
  ? new Intl.DateTimeFormat('uz-UZ', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value + 'T12:00:00'))
  : 'Muddat belgilanmagan';
export function tashkentToday() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tashkent', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  return ['year', 'month', 'day'].map(key => parts.find(part => part.type === key)?.value).join('-');
}
