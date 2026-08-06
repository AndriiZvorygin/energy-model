export function ResearchText({ text }: { text: string | undefined }) {
  if (!text) return null
  const blocks = text.split(/\n\n+/)
  return (
    <div className="prose-research">
      {blocks.map((block, index) => {
        const lines = block.split('\n')
        if (lines.every((line) => line.startsWith('- '))) {
          return <ul key={index}>{lines.map((line) => <li key={line}>{inlineCode(line.slice(2))}</li>)}</ul>
        }
        return <p key={index}>{inlineCode(block)}</p>
      })}
    </div>
  )
}

function inlineCode(text: string) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g).map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link) return <a key={index} href={link[2]} target="_blank" rel="noreferrer" className="font-semibold text-petroleum underline underline-offset-2">{link[1]}</a>
    return part
  })
}
