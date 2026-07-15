import type { ReactNode } from 'react'

export function PageHeader({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: ReactNode }) {
  return (
    <header className="border-b border-stone-200 bg-white px-5 py-10 sm:px-8 lg:px-12 lg:py-14 dark:border-stone-800 dark:bg-[#151c1a]">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs font-semibold uppercase tracking-widest text-petroleum">{eyebrow}</p>
        <h1 className="mt-3 max-w-4xl text-3xl font-semibold leading-tight text-ink sm:text-4xl dark:text-white">{title}</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600 sm:text-lg dark:text-stone-300">{description}</p>
        {children}
      </div>
    </header>
  )
}

export function PageBody({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 lg:px-12 lg:py-14">{children}</div>
}
