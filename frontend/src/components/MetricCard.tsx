import type { ReactNode } from 'react'
import { ArrowUpRight, BarChart3, Database, FlaskConical, Timer } from 'lucide-react'

const icons = { experiments: FlaskConical, datasets: Database, records: BarChart3, duration: Timer }
export function MetricCard({ label, value, change, tone = 'lime', icon }: { label: string; value: string; change: string; tone?: 'lime' | 'violet' | 'rose' | 'blue'; icon: keyof typeof icons }) {
  const Icon = icons[icon]
  const colors = { lime: 'bg-lime/10 text-lime', violet: 'bg-violet/10 text-violet', rose: 'bg-rose/10 text-rose', blue: 'bg-sky-400/10 text-sky-300' }
  return <div className="rounded-2xl border border-line bg-panel p-4 shadow-glow"><div className="mb-5 flex items-start justify-between"><div className={`grid h-9 w-9 place-items-center rounded-xl ${colors[tone]}`}><Icon size={17} /></div><ArrowUpRight size={15} className="text-muted" /></div><div className="text-[11px] font-bold uppercase tracking-[.12em] text-muted">{label}</div><div className="mt-1 flex items-end justify-between"><div className="text-2xl font-extrabold tracking-tight">{value}</div><div className="text-[11px] font-bold text-lime">{change}</div></div></div>
}

export function SectionTitle({ eyebrow, title, action }: { eyebrow?: string; title: string; action?: ReactNode }) {
  return <div className="mb-5 flex items-end justify-between"><div>{eyebrow && <div className="mb-1 text-[10px] font-bold uppercase tracking-[.18em] text-lime">{eyebrow}</div>}<h2 className="text-lg font-extrabold tracking-tight">{title}</h2></div>{action}</div>
}
