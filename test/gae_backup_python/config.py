# coding: utf-8

BACKUP_NAME = 'gae_backup_'

# back up entity kinds.
# BACKUP_KINDS = '*' # back up all kinds. except starts with '_' entities.
# BACKUP_KINDS = 'Model1'
# BACKUP_KINDS = ['Model1', 'Model2']
BACKUP_KINDS = '*'

# backup filesystem. 'gs' is Google Cloud Storage or blank is Blobstore
BACKUP_FILESYSTEM = 'gs'

BACKUP_GS_BUCKET_NAME = 'gae-backup-python-test.appspot.com'

# Delete backup files after n days
BACKUP_EXPIRE_DAYS = 3
