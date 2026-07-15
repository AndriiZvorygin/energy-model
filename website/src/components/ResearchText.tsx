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
  return text.split(/(`[^`]+`)/g).map((part, index) => part.startsWith('`') && part.endsWith('`')
    ? <code key={index}>{part.slice(1, -1)}</code>
    : part)
}
