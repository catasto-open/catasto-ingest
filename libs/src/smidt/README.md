# Smidt

## How to use the library

```python
❯ ipython
Python 3.10.7 (main, Oct 18 2022, 18:24:49) [Clang 14.0.0 (clang-1400.0.29.102)]
Type 'copyright', 'credits' or 'license' for more information
IPython 8.20.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: from smidt.watcher import MyFTPEventHandler, FTPPollingObserver

In [2]: ftp_url = "ftp://user:password@127.0.0.1/smidt"

In [3]: from fs import open_fs

In [4]: from smidt.client import FTPConfig, FTPDriver, FTPClient

In [5]: ftp_config = FTPConfig()

In [6]: driver = FTPDriver(config=ftp_config)

In [7]: ftp_client = FTPClient(driver=driver)

In [8]: event_handler = MyFTPEventHandler(open_fs(ftp_url), ftp_client)

In [9]: observer = FTPPollingObserver(ftp_url, event_handler)

In [10]: try:
            observer.start()
            while True:
               time.sleep(1)
         except KeyboardInterrupt:
            observer.stop()

         observer.join()
```

This prints all the file created since the last timestamp written in the `LASTEVENT.txt`
file that is placed in the directory configured for observing the events.
