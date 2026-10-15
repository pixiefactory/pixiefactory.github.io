# pixiefactory.github.io

Static site for [Pixie's Factory](https://pixiefactory.github.io): Pixie the robot posts one source-checked fun fact a day as a YouTube Short. GitHub Pages serves this user site from the `main` branch root. An empty `.nojekyll` file tells Pages to publish the files as-is, with no Jekyll build.

`config.json` holds the public `base_url` (`https://pixiefactory.github.io`), the YouTube channel links, and the tagline. Fact copy lives in `facts.json`; each fact has a page under `facts/`.

## Adding a fact

From the repo root, `add_fact.py` reads an upload notes file, pulls a thumbnail from the Short, and rebuilds the site:

```bash
python3 add_fact.py path/to/upload.md --video path/to/short.mp4 --date 2026-10-16 \
    [--script path/to/script.json] [--slug bananas-are-berries] [--frame 3] [--youtube-id ID]
```

It writes or updates that fact in `facts.json`, then regenerates `facts/<slug>.html`, the home-page fact grid in `index.html`, `sitemap.xml`, and `robots.txt`.

To regenerate those pages from the current `facts.json` without adding a fact:

```bash
python3 add_fact.py --rebuild
```

To attach a YouTube ID later, set `"youtube_id"` for that fact in `facts.json` and run `--rebuild`, or edit the single `data-youtube-id` attribute on the fact's HTML page.
