export function ChartControls({ range, onRange, onReset }: { range: string; onRange: (range: string) => void; onReset: () => void }) {
  return <div className="flex flex-wrap items-center gap-2" aria-label="Chart controls">
    {['5y', '10y', '20y', 'all'].map((item) => <button key={item} type="button" onClick={() => onRange(item)} className={`border px-3 py-2 text-xs font-semibold ${range === item ? 'border-petroleum bg-petroleum text-white' : 'border-stone-300 dark:border-stone-700'}`}>{item === 'all' ? 'Full history' : item.toUpperCase()}</button>)}
    <button type="button" onClick={onReset} className="border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700">Reset view</button>
  </div>
}
