import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const args = process.argv.slice(2)
function argument(name) {
  const index = args.indexOf(name)
  return index >= 0 ? args[index + 1] : undefined
}

const usageDir = path.resolve(argument('--usage-dir') ?? process.env.PYA_OLLAMA_USAGE_DIR ?? path.resolve(projectRoot, '../pyash/world/house/web-assistant/artifacts/manual/ollama/usage'))
const outputPath = path.resolve(argument('--output') ?? path.join(projectRoot, 'data/seed/local_ollama_usage_monthly.csv'))
const helperPath = path.resolve(process.env.PYASH_OLLAMA_USAGE_HELPER ?? path.resolve(projectRoot, '../pyash/program/library/ollama_usage.mjs'))
const { listOllamaUsageRecords } = await import(pathToFileURL(helperPath).href)
const records = await listOllamaUsageRecords(usageDir)
const grouped = new Map()
for (const record of records) {
  const month = String(record.started_at ?? '').slice(0, 7)
  if (!/^\d{4}-\d{2}$/u.test(month)) continue
  const model = String(record.resolved_model || record.model || 'unknown').trim() || 'unknown'
  const key = `${month}\u0000${model}`
  const row = grouped.get(key) ?? { month, model, calls: 0, completed_calls: 0, failed_calls: 0, prompt_tokens: 0, output_tokens: 0 }
  row.calls += 1
  if (record.status === 'completed') row.completed_calls += 1
  else row.failed_calls += 1
  row.prompt_tokens += Number(record.prompt_eval_count) || 0
  row.output_tokens += Number(record.eval_count) || 0
  grouped.set(key, row)
}

const columns = ['month', 'model', 'calls', 'completed_calls', 'failed_calls', 'prompt_tokens', 'output_tokens']
const csvCell = (value) => `"${String(value).replaceAll('"', '""')}"`
const lines = [columns.join(','), ...[...grouped.values()]
  .sort((left, right) => left.month.localeCompare(right.month) || left.model.localeCompare(right.model))
  .map((row) => columns.map((column) => csvCell(row[column])).join(','))]
await fs.mkdir(path.dirname(outputPath), { recursive: true })
await fs.writeFile(outputPath, `${lines.join('\n')}\n`, 'utf8')
console.log(`Wrote ${grouped.size} monthly model aggregates from ${records.length} usage records.`)
