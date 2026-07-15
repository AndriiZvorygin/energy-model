# Energy Model Educational Website

## Purpose

This Node.js/TypeScript application explains the Energy Model for human readers. It presents global liquidity, benchmark and realised oil prices, comparative inventory, tradable oil exposure, equities, energy throughput, and economic activity as related analytical layers.

The website is an educational research atlas, not a trading dashboard. It does not run models or fetch research data in the browser.

## Relationship to the Python Pipeline

The Python package under `../oil_model/` owns data acquisition, transformations, model estimation, validation, Markdown findings, CSV summaries, and PNG chart generation.

The website build runs `scripts/generate-data.mjs`, which:

- reads selected CSV files from `../analysis/`;
- extracts relevant sections from generated Markdown reports;
- writes the typed presentation module `src/data/generated.ts`;
- copies selected generated charts from `../charts/` to `public/charts/`.

The website is therefore downstream of the research pipeline. It must not change the locked model or existing analysis outputs.

## Local Development

Requirements:

- Node.js 20 or newer
- npm
- generated project files under `../analysis/` and `../charts/`

From `website/`:

```bash
npm install
npm run dev
```

The `predev` script refreshes the website data module and chart copies before starting Vite. The development server prints its local URL in the terminal.

## Build Process

Create a production build:

```bash
npm install
npm run build
```

The build performs these steps:

1. regenerate website data from the existing research artifacts;
2. type-check the TypeScript application;
3. create an optimized static site under `website/dist/`.

Preview the production build locally:

```bash
npm run preview
```

For repeatable CI installations, use `npm ci` instead of `npm install`.

## Deployment

For the GitHub Pages project path `AndriiZvorygin/energy-model`, run:

```bash
npm ci
npm run build:pages
```

Deploy the contents of `website/dist/`. The `build:pages` script configures Vite and React Router for the `/energy-model/` base path.

For a root-domain deployment, use the standard `npm run build`. For a custom subpath such as `andrii.zvorygin.ca/energy-model`, use:

```bash
npm run build -- --base /energy-model/
```

The host should serve `index.html` as the fallback for client-side routes. See [../docs/deployment.md](../docs/deployment.md) for GitHub Pages workflow guidance and custom-domain details.

## Refreshing Research Content

When research outputs are intentionally updated, run from the repository root:

```bash
.venv/bin/python -m oil_model.pipeline --root .
.venv/bin/python -m oil_model.verify_release --root .
cd website
npm run build
```

Review changes to `src/data/generated.ts` and `public/charts/` before publication.
