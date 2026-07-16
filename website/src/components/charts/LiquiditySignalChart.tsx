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

  return <section aria-label="Liquidity and oil model views">
    <div className="mb-5 border-l-2 border-petroleum pl-4">
      <fieldset>
        <legend className="mb-2 text-xs font-semibold uppercase text-stone-500">Research view</legend>
        <div className="inline-flex flex-wrap border border-stone-300 dark:border-stone-700">
          {views.map((item) => <button key={item.id} type="button" onClick={() => setView(item.id)} aria-pressed={view === item.id} className={`px-3 py-2 text-xs font-semibold ${view === item.id ? 'bg-petroleum text-white' : 'bg-white text-ink dark:bg-stone-950 dark:text-white'}`}>{item.label}</button>)}
        </div>
      </fieldset>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">{selected.description}</p>
    </div>

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
      />
    )}
  </section>
}
