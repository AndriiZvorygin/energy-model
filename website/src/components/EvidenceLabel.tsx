type EvidenceLabelProps = {
  label: string
}

const tones: Record<string, string> = {
  'Validated relationship': 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200',
  'Supported historical pattern': 'border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-200',
  'Contextual indicator': 'border-stone-300 bg-stone-100 text-stone-700 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-200',
  'Experimental proxy': 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200',
  'Scenario concept': 'border-violet-300 bg-violet-50 text-violet-800 dark:border-violet-900 dark:bg-violet-950/40 dark:text-violet-200',
}

export function EvidenceLabel({ label }: EvidenceLabelProps) {
  return <span className={`inline-flex border px-2 py-1 text-xs font-semibold ${tones[label] ?? tones['Contextual indicator']}`}>{label}</span>
}
