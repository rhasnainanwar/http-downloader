# HTTP Downloader
**usage: client.py [-h] [-r] -n NUM -i INTERVAL -c CONNECTION -f SRC -o DEST**

```optional arguments:
  -h, --help            show this help message and exit
  -r, --resume          Whether to resume the existing download in progress

required arguments:
  -n NUM, --num NUM      Total number of simultaneous connections
  -i INTERVAL, --interval INTERVAL
                        Time interval in seconds between metric reporting
  -c CONNECTION, --connection CONNECTION
                        Type of connection: UDP or TCP
  -f SRC, --src SRC     Address pointing to the file location on the web
  -o DEST, --dest DEST  Address pointing to the location where the file is downloaded```
