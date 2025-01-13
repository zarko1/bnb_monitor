# BNB Monitoring
Scripts and html for BNB monitoring.

# Installation

## Get code from git

Go to your workdir where your scripts will be running and clone git:
```bash
git clone git@github.com:zarko1/bnb_monitor.git
```

## Setup python

Create a venv
```bash
python -m venv venv
```
activate
```bash
source venv/bin/activate
```
and install pandas
```bash
pip install pandas
```

## Setup web page

Copy ./web and its content to the web server.

## Setup cron

Install crontab (example in scripts/crontab):
```
05 * * * * PATH_TO_YOUR_WORK_DIR/scripts/cronJob.sh >> PATH_TO_YOUR_WORKDIR/log/cron.log 2>&1
```
If you haven't done it before run kcroninit to get the kerberos ticket for your cron jobs. 

## Modify paths
Update the $WORKDIR and $WEBDATA paths in the scripts/cronJob.sh script.

## Create directories
Default setup will need $WORKDIR/data, $WORKDIR/log and $WEBDATA

# Running getHourlyData.py

The cron job will run this hourly, and create and copy the output file to $WEBDATA directory. Note that html looks in ./data/beam_data_hourly.csv . If you make changes to the output name or path make corresponding changes in the html file.

Options for <span>getHourlyData.py<span>:
```
> ./getHourlyData.py -h
usage: getHourlyData.py [-h] [-o OUTPUT_FILE] [-s START_DATE] [-d]

Get beam data and store it for bnb monitor web page.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Ouptut csv file.
  -s START_DATE, --start-date START_DATE
                        Starting from this date. Used only when starting new file, otherwise just appending to existing date. Should be in format YYYY-MM-DD, like 2024-12-09.
  -d, --debug           Prints out more info.

```



