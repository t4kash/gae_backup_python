Scheduled backup script for GAE datastore
=========

## Synopsis
Scheduled backup script for google app engine python application.
Using Datastore Admin.
* Back up specifies kinds or all kinds
* Delete old backups

## Installation

### Enable Datastore admin

App engine console > Datastore Admin

### Copy to this scripts

```bash
cp -r gae_backup_python your_application/.
```

### Add url handler to app.yaml

```app.yaml
handlers:
- url: /gae-backup
  script: gae_backup_python.backup.app
  login: admin
```

### Add scheduled task to cron.yaml

```cron.yaml
cron:
- description: backup job
  url: /gae-backup
  schedule: every day 02:00
```

### Edit config.py

Edit BACKUP_FILESYSTEM and BACKUP_EXPIRE_DAYS and others.

### Deploy your application and update_cron


## License
This software is released under the MIT License, see LICENSE.
