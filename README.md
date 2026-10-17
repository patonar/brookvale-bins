# Brookvale Bins

A public subscription calendar for alternating Wednesday collections: **general waste on 21 October 2026**, **recycling on 28 October 2026**, then alternating weekly for two calendar years (through 20 October 2028, inclusive). The last scheduled collection is 18 October 2028: 105 all-day events.

- Website: https://patonar.github.io/brookvale-bins/
- Calendar feed: https://patonar.github.io/brookvale-bins/brookvale-bins.ics

## Develop

Python 3.12+; standard library only. Use the existing checkout; no extra worktree is necessary.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/generate.py
python3 -m http.server 8000 --directory _site
```

Generated files are in ignored `_site/`. No credentials, packages, database, or external services are needed to build. The webpage reads the CSV to display the next collection.

## Change an exceptional date

Edit `collections.csv`, changing only the `date` cell for the affected event (ISO `YYYY-MM-DD`). **Keep its `event_id` unchanged**, even when the date no longer matches the identifier. This preserves calendar identity so subscribers receive an update instead of a duplicate. Collection values are `General waste` and `Recycling`. Preserve the three-column format. Rows can be reordered; the generator sorts actual dates. Keep IDs unique and do not reuse deleted IDs.

The default-schedule test checks a baseline fixture; exceptional dates in the CSV do not break that test. The published-CSV test checks valid, unique events, and the exception test verifies identity preservation. To extend the calendar, append new rows with new permanent IDs and update the coverage text and schedule test.

The feed uses UTC modification timestamps, CRLF line endings, UTF-8 line folding, stable UIDs, and date-only DTSTART / exclusive next-day DTEND. It publishes concrete events instead of recurrence rules, allowing each date to move independently. Subscription refresh timing is controlled by the calendar provider. Downloading the feed once does not subscribe. Users configure their own notification reminders.

## Publish

Push to `main` to run `.github/workflows/pages.yml`: test, generate, upload, and deploy using GitHub Pages Actions and OIDC. No personal access token is stored in this repository.

In GitHub repository **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**. If Actions are disabled, enable them in **Settings → Actions → General** and permit the official actions referenced in the workflow. Run **Actions → Deploy Brookvale Bins → Run workflow** if needed after enabling Pages. Check the successful deployment, then request both public URLs above. Publication is only verified when both return HTTP 200 and the feed contains the expected events.
