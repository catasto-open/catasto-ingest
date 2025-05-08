# Smidt

## How to use the library

Configure your settings in a file `.env_smidt` using a copy of the sample env file `sample.env_smidt `.

Run the following example script:

```shell
❯ poetry run python smidt/app.py
````

In the standard output you will see the following messages about the copy of the latest files from the FTP server to MinIO:

```shell
19:20:36 | DEBUG    | Verified access to bucket: ftp-backup

19:20:43 | INFO     | Starting monitoring of directory: /entrate

19:20:43 | INFO     | Backup configured to MinIO bucket: ftp-backup

19:20:48 | DEBUG    | Read lock timestamp: 2025-01-06 19:36:18.868941

19:20:54 | INFO     | Processing 2 new files

19:21:00 | INFO     | Backed up ATASR06.S0044860.D2025007.T021431.p7m.enc (3783546 bytes) to MinIO: 2025/01/12/created/ATASR06.S0044860.D2025007.T021431.p7m.enc

19:21:01 | INFO     | Backed up ATASR06.S0044860.D2025007.T021433.p7m.enc (180806 bytes) to MinIO: 2025/01/12/created/ATASR06.S0044860.D2025007.T021433.p7m.enc

19:21:02 | DEBUG    | Updated lock timestamp: 2025-01-12 19:20:43.233970

19:21:02 | INFO     | created: ATASR06.S0044860.D2025007.T021431.p7m.enc at 2025-01-07 06:20:00

19:21:02 | INFO     | created: ATASR06.S0044860.D2025007.T021433.p7m.enc at 2025-01-07 06:20:00

19:21:02 | DEBUG    | Waiting 600 seconds
```

This prints all the files processed and copied since the last timestamp written in the lock file that is placed in the directory configured for observing the events.
