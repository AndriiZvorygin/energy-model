import type { LucideIcon } from 'lucide-react'

type MetricCardProps = {
  label: string
  value: string
  detail: string
  icon: LucideIcon
  tone?: 'petroleum' | 'signal' | 'inventory' | 'equity'
}

const tones = {
  petroleum: 'text-petroleum bg-petroleum/10 dark:bg-petroleum/20',
  signal: 'text-signal bg-signal/10 dark:bg-signal/20',
  inventory: 'text-inventory bg-inventory/10 dark:bg-inventory/20',
  equity: 'text-equity bg-equity/10 dark:bg-equity/20',
}

export function MetricCard({ label, value, detail, icon: Icon, tone = 'petroleum' }: MetricCardProps) {
  return (
    <article className="min-h-40 border border-stone-200 bg-white p-5 shadow-quiet dark:border-stone-800 dark:bg-[#18201d]">
      <div className={`mb-5 flex h-9 w-9 items-center justify-center rounded-md ${tones[tone]}`}>
        <Icon aria-hidden="true" size={18} />
      </div>
      <p className="text-xs font-semibold uppercase tracking-widest text-stone-500 dark:text-stone-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold tabular-nums text-ink dark:text-white">{value}</p>
      <p className="mt-2 text-sm leading-5 text-stone-600 dark:text-stone-400">{detail}</p>
    </article>
  )
}
