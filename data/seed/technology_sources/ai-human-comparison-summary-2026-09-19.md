# AI and human capability: dated summary

**Evidence retrieved:** 19 September 2026

**Normalized records:** 113

**Source URLs archived:** 82, with 75 downloaded successfully

**IQ scores used:** none

## What the data support

- Current frontier systems are already **superhuman on selected tasks**. The claim is task-specific: GDPval records expert-rated model deliverables that match or exceed the expert deliverable on a substantial subset; technical benchmark scores are very high on some coding and mathematical tasks.
- Current systems are **not broadly superintelligent**. Performance remains uneven across academic reasoning, interactive abstraction, technical work, professional deliverables, long-horizon agents, social context, and physical action.
- Open-weight models are genuine downloadable systems, not only cheaper hosted APIs. The archive includes Qwen3.8-27B, DeepSeek-V4-Pro, Kimi K3, GLM-5.3, Mistral Small 4, gpt-oss-120b, Gemma 4 12B, and Llama 4 Maverick. Their licences range from Apache-2.0 and MIT to custom licences.
- Open-weight and closed results cannot be ranked from a bare score alone. Reasoning effort, tool use, scaffolding, sampling, context, hardware, and evaluation date change the result.
- GDPval gives the clearest economic evidence: it uses realistic deliverables across 44 occupations, grades them against work produced by experienced professionals, and reports model speed and API-cost advantages. Human review, iteration, integration, and ownership costs remain outside the headline speed/cost ratio.
- ARC-AGI-2’s paper reports 75% human task-level success and 66% human test-pair success; a separate 100% figure means every final task was solved by at least two testers. GPT-6 Astra scores 95.0% on the archived semi-private evaluation.
- METR measures an agent system’s ability to complete tasks calibrated by human expert time. It is a capability horizon for a technical scaffold, not a general intelligence number.

## Human comparison in one table

| Area | Human reference | Current model evidence | What it shows |
|---|---|---|---|
| GPQA full / Diamond | Full set: PhD experts 65%, skilled non-experts 34%, random 25%. Diamond Table 2: experts 81.3%, skilled non-experts 22.1% | Current Diamond scores up to 96.0% | Very high performance on a hard closed question set; Diamond human figures are selection-filtered subset references |
| HLE | No published single human accuracy | GPT-6 Astra 54.80%; Fable 5.1 46.50%; Gemini 3.8 Flash 44.52% | Difficult expert-authored questions remain far from saturation |
| AIME | Competition context; no single comparable human score | gpt-oss-120b high: 95.8% AIME 2024, 92.5% AIME 2025 without tools | Strong mathematical performance; effort and tools matter |
| ARC-AGI-2 | Humans: 75% task-level, 66% test-pair aggregate | GPT-6 Astra 95.0%; GPT-5.6 Sol 92.5% | Current model scores exceed the paper’s task-level human aggregate on this benchmark |
| GDPval | Expert work product in paired blind grading | Claude Opus 4.1 better-or-equal to expert in 47.6% of gold tasks | Models already produce useful professional work; human comparison remains central |
| METR | Human task duration calibrates difficulty | p50 horizons reach many hours for some agent systems | Agent systems handle longer clean technical tasks; the suite is domain-limited |

## Bottom line

The data replace “AI IQ” with a more useful statement:

> Current AI systems have superhuman performance on some tightly specified tasks and useful, measurable performance across software and knowledge work. They remain uneven across domains and do not demonstrate broad superintelligence.

The CSV and JSON files preserve the conditions needed to evaluate that statement later: benchmark version, tool access, reasoning effort, sampling, scaffolding, human reference, source type, publication date, retrieval timestamp, and source hash.
