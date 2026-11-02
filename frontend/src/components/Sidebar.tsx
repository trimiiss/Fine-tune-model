import { BookOpen, Bot, Database, FlaskConical, LayoutDashboard, Menu, Settings2, Sparkles, X } from 'lucide-react'
import type { View } from '../types'

const nav: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'datasets', label: 'Datasets', icon: Database },
  { id: 'training', label: 'Fine-tune', icon: FlaskConical },
  { id: 'playground', label: 'Playground', icon: Bot },
  { id: 'history', label: 'Experiment history', icon: BookOpen },
]

export function Sidebar({ view, setView, open, setOpen }: { view: View; setView: (view: View) => void; open: boolean; setOpen: (open: boolean) => void }) {
  return <>
    <button className="fixed left-4 top-4 z-30 rounded-lg border border-line bg-panel p-2 text-muted lg:hidden" onClick={() => setOpen(true)}><Menu size={18} /></button>
    {open && <button aria-label="Close menu" className="fixed inset-0 z-20 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-30 flex w-[248px] flex-col border-r border-line bg-[#0C0F15] px-4 py-5 transition-transform lg:static lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="mb-10 flex items-center justify-between px-2">
        <div className="flex items-center gap-3"><div className="grid h-8 w-8 place-items-center rounded-xl bg-lime text-canvas"><Sparkles size={17} strokeWidth={2.5} /></div><div><div className="text-sm font-extrabold tracking-tight">Fine-Tuning</div><div className="text-[11px] font-semibold text-muted">STUDIO / LOCAL LAB</div></div></div>
        <button className="text-muted lg:hidden" onClick={() => setOpen(false)}><X size={18} /></button>
      </div>
      <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-muted">Workspace</div>
      <nav className="space-y-1">
        {nav.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => { setView(id); setOpen(false) }} className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${view === id ? 'bg-[#1B222A] text-ink shadow-[inset_3px_0_0_#C9F27A]' : 'text-muted hover:bg-[#151A22] hover:text-ink'}`}><Icon size={17} className={view === id ? 'text-lime' : 'text-muted group-hover:text-ink'} />{label}{id === 'playground' && <span className="ml-auto rounded-full bg-violet/15 px-1.5 py-0.5 text-[9px] font-bold text-violet">NEW</span>}</button>)}
      </nav>
      <div className="mt-auto">
        <div className="mb-5 rounded-2xl border border-line bg-panel p-3.5"><div className="mb-2 flex items-center justify-between"><span className="text-[11px] font-bold text-muted">LOCAL RUNTIME</span><span className="flex items-center gap-1 text-[10px] font-bold text-lime"><span className="h-1.5 w-1.5 rounded-full bg-lime" />ONLINE</span></div><div className="mb-3 text-xs text-ink">Ready for a new experiment</div><div className="h-1.5 overflow-hidden rounded-full bg-[#252C37]"><div className="h-full w-[72%] rounded-full bg-lime" /></div><div className="mt-1.5 flex justify-between text-[10px] text-muted"><span>Memory headroom</span><span>72%</span></div></div>
        <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-muted hover:bg-[#151A22] hover:text-ink"><Settings2 size={17} />Settings</button>
        <div className="mt-5 flex items-center gap-3 border-t border-line px-2 pt-5"><div className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-violet to-rose text-xs font-extrabold text-white">TR</div><div className="min-w-0"><div className="truncate text-xs font-bold">Trimi</div><div className="truncate text-[10px] text-muted">local workspace</div></div><div className="ml-auto h-1.5 w-1.5 rounded-full bg-lime" /></div>
      </div>
    </aside>
  </>
}
