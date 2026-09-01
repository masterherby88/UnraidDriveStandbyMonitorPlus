# Unraid Drive Standby Monitor Plus

Fork of **EldonMcGuinness/UnraidDriveStandbyMonitor** with extra metrics and a configurable averaging window.

## What this plugin does

The plugin periodically samples the spin state of your drives (standby vs active) and stores the result in a small SQLite DB.
From that data it shows:

- **Standby %** (how much of the monitored time a drive spent in standby)
- **Spinup metrics** (derived from standby→active transitions)
  - **Spinups today** (count)
  - **Average spinups/day** (over the configured window)
  - **Max spinups in a day** (over the configured window)

## Where to find it in Unraid

### Unraid → Main (Tab: Standby Averages)

Adds extra columns to the existing table view:

- `Spinups (avg)`
- `Spinups (max/day)`
- `Spinups (today)`

### Unraid → Tools → DriveStandbyMonitor

This page is used as the **single source of truth** for the averaging window.

- Choose the **Average Window**: `1 / 3 / 7 / 14 / 30 / 90 / 365` days
- Click **Save**

The value is persisted to:

- `/boot/config/plugins/DriveStandbyMonitor/settings.cfg`

Main uses the same setting automatically (no second dropdown).

## How spinups are counted (important)

This plugin does not read SMART spin-up counters.
Instead, **spinups are inferred** by counting **standby → active transitions** in the sampled data (0→1 state changes).

That means:

- It matches what you actually care about ("drive woke up")
- Very short sleep/wake cycles *could* be missed if they happen between two samples

## Notes / Compatibility

- The sampling is done via a cron job (default every 15 minutes).
- The DB is kept for ~30 days (as in upstream).
- No schema changes were introduced for the spinup metrics (computed from the existing table).

## Credits

- Original plugin: https://github.com/EldonMcGuinness/UnraidDriveStandbyMonitor
- This fork: adds spinup metrics + persistent averaging window
