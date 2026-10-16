# Backups

Every backup is a snapshot of one app's data: its database, its media folder (the Comms studio's uploads), and a manifest listing how many rows each table holds. Right after writing it, beanagileorg unpacks the backup into a scratch folder and checks it: SQLite's integrity check, the same row count in every table, and the same files. A backup only counts as good if it passes. The result is shown next to each backup in the app's Settings and in `beanagileorg backups`.

Backups hold the same private data as the apps, so keep them somewhere just as safe: an encrypted disk (FileVault) or an encrypted external drive.

## Commands

```bash
beanagileorg backup all
```

Backs up every app that has data, checks each backup, and keeps the newest 30 per app (`--keep 60` to keep more).

```bash
beanagileorg backups toolkit
```

Lists the toolkit's backups and whether each one passed its check.

```bash
beanagileorg verify ~/.beanagileorg/backups/toolkit/toolkit-20261102-020000.tar.gz
```

Checks one backup without changing anything.

```bash
beanagileorg restore ~/.beanagileorg/backups/toolkit/toolkit-20261102-020000.tar.gz --app toolkit
```

Puts a backup back. Stop the app first. The backup is checked before anything changes, and your current data is moved into a `before-restore-<time>` folder inside the app's data folder, not deleted.

The app's Settings screen also has a **Back up now** button and shows the last ten backups.

## Where backups go

`~/.beanagileorg/backups/<app>/` by default. To keep them elsewhere, such as an external drive, set `BEANAGILEORG_BACKUP_DIR`:

```bash
export BEANAGILEORG_BACKUP_DIR="/Volumes/[Placeholder drive name]/beanagileorg-backups"
```

## Nightly backups

```bash
beanagileorg schedule
```

Prints a macOS launchd job that runs `beanagileorg backup all` at 2:00 every night (`--hour` and `--minute` to change it). If the Mac is asleep at that time, launchd runs it when the Mac wakes. To save and turn it on:

```bash
beanagileorg schedule --write
```

```bash
launchctl load ~/Library/LaunchAgents/org.beanagileorg.backup.plist
```

Run `beanagileorg schedule --write` from the same shell settings you run the apps with, since it records `BEANAGILEORG_DATA` and `BEANAGILEORG_BACKUP_DIR` if they are set. Output goes to `~/.beanagileorg/backups/launchd.log`. To turn it off:

```bash
launchctl unload ~/Library/LaunchAgents/org.beanagileorg.backup.plist
```

## Test a restore now and then

The automatic check proves each backup unpacks and matches. Once a month, also do a real restore into a scratch copy and open the app on it:

```bash
BEANAGILEORG_DATA=/tmp/beanagileorg-restore-test beanagileorg restore [path to a backup] --app toolkit --force
```

```bash
BEANAGILEORG_DATA=/tmp/beanagileorg-restore-test beanagileorg toolkit --port 8811
```

Sign in at http://127.0.0.1:8811 with your usual password, look around, then stop it and delete `/tmp/beanagileorg-restore-test`.
