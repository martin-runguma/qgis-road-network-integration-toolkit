# Road Network Integration Toolkit — website

A fast, dependency-free landing page for the **Road Network Merging and Alignment
Toolkit** QGIS plugin, built with modern HTML, CSS and vanilla JavaScript.

## Contents

```
index.html               single-page site
assets/css/site.css      design system, responsive layout and motion
assets/js/site.js        navigation, reveals, tabs, coverage explorer, log demo
assets/images/           plugin icon + SVG favicon
.github/workflows/       GitHub Pages deployment workflow
LICENSE                  GPL-3.0
robots.txt / sitemap.xml small SEO helpers
```

No build step, package manager or framework. Open `index.html` in a browser, or
serve the folder with any static server:

```bash
python -m http.server 8000
```

## What is interactive

- **Hero map layers** — toggle priority, secondary and buffer layers.
- **Method tabs** — accessible WAI-ARIA tabs, arrow/Home/End keyboard support.
- **Coverage explorer** — drag the slider to see the remaining ratio, class and
  whether the road is added. It reproduces the legacy thresholds, including the
  intentional gap at exactly `0.25`.
- **Class reference** — the active row follows the explorer.
- **Processing console** — an illustrative, looping log animation that starts
  when scrolled into view.
- **FAQ** — native `<details>` accordions.
- **Motion** — scroll reveals, staggered entrances, animated flow lines and
  count-up stats, all disabled under `prefers-reduced-motion`.

## Publishing to GitHub Pages

1. Create a repository, for example `qgis-road-network-integration-toolkit`.
2. Push the contents of this folder to the default branch:

   ```bash
   git init
   git add .
   git commit -m "Redesign toolkit website"
   git branch -M main
   git remote add origin https://github.com/<user>/<repo>.git
   git push -u origin main
   ```

3. In **Settings → Pages**, choose **GitHub Actions** as the source. The included
   workflow (`.github/workflows/pages.yml`) deploys on every push to `main`.
4. If you prefer **Deploy from a branch**, select `main` / `/ (root)` instead.
   The included `.nojekyll` keeps asset folders intact.

All asset links are relative, so the site works at a project subpath
(`https://<user>.github.io/<repo>/`) with no configuration.

## Content accuracy notes

- The hero map, method diagrams and interface illustrations are **conceptual**,
  not QGIS screenshots. Keep that caption if the artwork is replaced.
- The processing console is labelled illustrative; its values are examples, not
  measurements from a specific dataset.
- Version, compatibility, method descriptions and coverage thresholds follow the
  supplied 2.1.0 plugin metadata, README and methodology guide.
- The 33 interface languages are taken from `i18n.py` in the plugin package.

## Licence

The plugin and this website are released under the GNU General Public License
v3.0. See `LICENSE`.
