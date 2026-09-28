# rehnx terminal profile — setup

This package is designed to replace the visual layer of `rehnx/rehnx`.

## 1. Copy the files

Copy everything in this package into the root of your `rehnx/rehnx` repository.

If you want only this design, remove the old generator and old snake workflow:

```bash
rm -f scripts/profile_visuals.py
rm -f .github/workflows/snake.yml
```

The included `.gitignore` keeps your source photo, preprocessed portrait, virtual environment, and Python cache out of Git.

## 2. Generate your real ASCII portrait

Put a photo in the repository root as:

```text
source-photo.jpg
```

A front-facing or three-quarter portrait with simple lighting works best.

Create a local environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r scripts/requirements-portrait.txt
```

Preprocess the image:

```bash
python scripts/prep_photo.py source-photo.jpg
```

Generate the animated SVG:

```bash
python scripts/make_ascii_svg.py
```

This replaces the included `ascii-portrait.svg` placeholder.

## 3. Generate the info card

Edit the `PROFILE` dictionary near the top of:

```text
scripts/make_info_card.py
```

Then run:

```bash
python scripts/make_info_card.py
```

## 4. Test the contribution graph locally

Install only the lightweight daily dependencies:

```bash
pip install -r scripts/requirements.txt
```

Fetch your public contribution calendar:

```bash
python scripts/fetch_contributions.py --username rehnx
python scripts/render_heatmap_svg.py
```

No personal access token is required for fetching the public contribution calendar.

## 5. Commit and push

```bash
git add .
git commit -m "feat: terminal profile"
git push
```

The workflow also runs after changes to the profile scripts/workflow, so the contribution placeholder should be replaced automatically after the push.

You can also run it manually from:

```text
GitHub → rehnx/rehnx → Actions → Update terminal profile → Run workflow
```

## Daily refresh

`.github/workflows/update-profile-art.yml` runs every day at approximately 06:17 UTC.

It:

1. installs only `requests` and `beautifulsoup4`;
2. scrapes `https://github.com/users/rehnx/contributions`;
3. writes `data/contributions.json`;
4. renders `contrib-heatmap.svg`;
5. commits the two generated files only when they changed.

The workflow uses the repository's built-in GitHub Actions credentials for `git push`; you do not need to create or store a PAT.

## Static SVG previews

For tools that do not play SVG animation:

```bash
STATIC=1 python scripts/make_info_card.py
STATIC=1 python scripts/make_ascii_svg.py
STATIC=1 python scripts/render_heatmap_svg.py
```

Run the same command again without `STATIC=1` before committing if you want the animated version.
