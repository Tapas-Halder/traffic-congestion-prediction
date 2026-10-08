# Collection status

GitHub Actions writes `last_successful_collection_utc.txt` after a successful API collection run.

If this file does not change after a scheduled time, check the GitHub Actions workflow run and its logs. A scheduled workflow is not a hard real-time timer.
