# Website Deployment

The educational website is a static Vite application under `website/`. It reads generated research artifacts during the build and does not require a Python server in production.

## Local Development

Install dependencies and start Vite:

```bash
cd website
npm install
npm run dev
```

Vite runs on localhost, normally at:

```text
http://localhost:5173/energy-model/
```

The configured `/energy-model/` base matches the production repository path. Visiting the root development address printed by Vite redirects to the configured application base.

## Production Build

Before building, verify that the intended files under `analysis/` and `charts/` exist. Then run:

```bash
cd website
npm install
npm run build
```

The optimized static site is written to `website/dist/`. The build also creates `dist/404.html`, allowing GitHub Pages to return the React application shell for direct requests to client-side routes.

## GitHub Pages

Deployment is defined in `.github/workflows/deploy-pages.yml`. It runs automatically after pushes to `main` and can also be started through **Run workflow** in the GitHub Actions interface.

The workflow:

1. checks out the repository;
2. configures Node.js and GitHub Pages;
3. runs `npm install` in `website/`;
4. runs `npm run build`;
5. uploads `website/dist/` as the Pages artifact;
6. deploys the artifact through the official GitHub Pages action.

One repository setting is required:

1. Open the `AndriiZvorygin/energy-model` repository on GitHub.
2. Select **Settings**.
3. Select **Pages** under **Code and automation**.
4. Under **Build and deployment**, set **Source** to **GitHub Actions**.

The deployment URL is:

```text
https://andriizvorygin.github.io/energy-model/
```

The Vite base path is `/energy-model/`, and React Router uses `import.meta.env.BASE_URL` as its basename. This keeps application routes and chart assets under the GitHub Pages project path.

## Custom Domain

The proposed custom-domain path is:

```text
https://andrii.zvorygin.ca/energy-model/
```

The existing production build also uses `/energy-model/`, so the generated files can be served at that path. Configure the web server to return `index.html` for client-side routes such as `/energy-model/liquidity` and `/energy-model/economy`.

If the website later moves to the root of a dedicated domain, override the build base:

```bash
cd website
npm run build -- --base /
```

## Updating Published Research

When the Python analysis changes intentionally:

```bash
.venv/bin/python -m oil_model.pipeline --root .
.venv/bin/python -m oil_model.verify_release --root .
cd website
npm run build
```

The website prebuild step regenerates `src/data/generated.ts` from selected CSV and Markdown files and copies selected PNGs into `website/public/charts/`. Review those generated presentation assets before publication.
