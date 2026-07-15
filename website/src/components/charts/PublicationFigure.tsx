import { ChartViewer } from '../ChartViewer'

export function PublicationFigure({ src, alt, title, description, source }: { src: string; alt: string; title: string; description: string; source: string }) {
  return <details className="border-t border-stone-200 pt-5 dark:border-stone-800"><summary className="cursor-pointer text-sm font-semibold">Publication figure</summary><div className="mt-5"><ChartViewer src={src} alt={alt} title={title} description={description} source={source} /></div></details>
}
