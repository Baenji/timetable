# Timetable to ICS Converter

Fetches the TH AB Data Science lecture schedule from HTML, filters it by group, and converts it to iCalendar format.

## Quick Start

```bash
pip install beautifulsoup4 ics requests tzdata
python timetable.py
```

## Configuration

Edit the variables at the top of `timetable.py`:
* **`DS_GROUP`** - Your group in the Data Science schedule (`1` or `2`); events marked only for the other group are skipped. Set to `None` to keep all groups
* **`URL_DS`** - Source webpage for the Data Science schedule (filtered by `DS_GROUP`)

## Output

Generates an ICS calendar file (`sd2023.ics`) with lecture events including:
* Course title, exact date, and time
* Location and additional descriptions (lecturer, etc.)
* Proper timezone handling (Europe/Berlin)

## Automation

A GitHub Actions workflow (`.github/workflows/update.yml`) runs daily at 03:00 UTC to automatically fetch the latest schedule, update the `sd2023.ics` file, and push changes to the repository.