# HTTP Downloader
```**usage: client.py [-h] [-r] -n NUM -i INTERVAL -c CONNECTION -f SRC -o DEST**

optional arguments:<br/>
  -h, --help            show this help message and exit<br/>
  -r, --resume          Whether to resume the existing download in progress<br/>

required arguments:<br/>
  -n NUM, --num NUM      Total number of simultaneous connections<br/>
  -i INTERVAL, --interval INTERVAL<br/>
                        Time interval in seconds between metric reporting<br/>
  -c CONNECTION, --connection CONNECTION<br/>
                        Type of connection: UDP or TCP<br/>
  -f SRC, --src SRC     Address pointing to the file location on the web<br/>
  -o DEST, --dest DEST  Address pointing to the location where the file is downloaded```
