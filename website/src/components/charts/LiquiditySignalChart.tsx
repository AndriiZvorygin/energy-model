import { useState } from 'react'
import { ResearchTimeSeriesChart } from './ResearchTimeSeriesChart'

type LiquidityView = 'actual' | 'zscore' | 'residual'

const views: Array<{ id: LiquidityView; label: string; description: string }> = [
  {
    id: 'actual',
    label: 'Actual YoY',
    description: 'Compare GM2 and oil momentum in year-over-year percentage terms. GM2 is shifted to the selected later comparison month.',
  },
  {
    id: 'zscore',
    label: 'Standardized z-score',
    description: 'Compare unusually high or low observations using each series\' fixed published historical mean and standard deviation.',
  },
  {
    id: 'residual',
    label: 'Residuals (GM2 removed)',
    description: 'Remove the rolling GM2-implied component and show only the difference: actual oil YoY minus the liquidity-implied YoY path.',
  },
]

export function LiquiditySignalChart() {
  const [view, setView] = useState<LiquidityView>('zscore')
  const selected = views.find((item) => item.id === view) ?? views[1]
  const controls = <div className="border-2 border-petroleum bg-petroleum/5 p-4 dark:bg-petroleum/10">
    <fieldset>
      <legend className="text-sm font-semibold uppercase text-ink dark:text-white">Chart display: choose one</legend>
      <div className="mt-3 grid gap-2 sm:grid-cols-3" role="tablist" aria-label="Liquidity chart display">
        {views.map((item) => <button key={item.id} type="button" role="tab" onClick={() => setView(item.id)} aria-selected={view === item.id} className={`min-h-14 border px-4 py-3 text-left text-sm font-semibold ${view === item.id ? 'border-petroleum bg-petroleum text-white shadow-sm' : 'border-stone-400 bg-white text-ink hover:border-petroleum dark:border-stone-600 dark:bg-stone-950 dark:text-white'}`}><span className="block">{item.label}</span>{view === item.id && <span className="mt-1 block text-xs font-normal text-white/85">Currently displayed</span>}</button>)}
      </div>
    </fieldset>
    <p className="mt-3 text-sm leading-6 text-stone-700 dark:text-stone-200">{selected.description}</p>
    <p className="mt-2 text-xs font-medium text-stone-500">Display mode and GM2 lead time are separate controls. Choose the display here, then choose 4 months, 5 months, or another lead below.</p>
  </div>

  return <section aria-label="Liquidity and oil model views">
    {view === 'residual' ? (
      <ResearchTimeSeriesChart
        key="residual"
        file="oil-residual-ci.json"
        initialSeries={['WTI_residual', 'Brent_residual']}
        initialTransformation="raw"
        syncUrl={false}
        inspectCrossLayer
        showNormalizationControls={false}
        lagControl
        dynamicGm2Residuals
        startAtSeries="GM2_YoY"
        primaryControls={controls}
        zeroLine
      />
    ) : (
      <ResearchTimeSeriesChart
        key={view}
        file="gm2-oil-lead.json"
        initialSeries={['GM2_shifted', 'WTI_YoY', 'Brent_YoY', 'RAC_composite_YoY']}
        initialTransformation={view === 'actual' ? 'raw' : 'zscore'}
        syncUrl={false}
        lagControl
        inspectCrossLayer
        showNormalizationControls={false}
        startAtSeries="GM2_YoY"
        primaryControls={controls}
      />
    )}
  </section>
}
