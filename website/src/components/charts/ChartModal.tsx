import { useEffect } from 'react'
import { X } from 'lucide-react'

export function ChartModal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    if (!open) return
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', close)
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', close); document.body.style.overflow = '' }
  }, [open, onClose])
  if (!open) return null
  return <div className="fixed inset-0 z-50 overflow-y-auto bg-black/65 p-3 sm:p-6" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
    <div className="mx-auto min-h-full max-w-6xl bg-paper p-4 shadow-2xl sm:p-7 dark:bg-[#111715]" onClick={(event) => event.stopPropagation()}>
      <div className="flex items-center justify-between gap-4"><h2 className="text-xl font-semibold">{title}</h2><button type="button" onClick={onClose} className="flex h-10 w-10 items-center justify-center border border-stone-300 dark:border-stone-700" aria-label="Close expanded chart"><X size={19} /></button></div>
      <div className="mt-5">{children}</div>
    </div>
  </div>
}
