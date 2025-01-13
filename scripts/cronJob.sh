#!/bin/bash

WORKDIR=/exp/sbnd/app/users/${USER}/work/bnbmon/
WEBDATA=/publicweb/z/${USER}/bnb_monitor/data
LOGFILE=$WORKDIR/log/ifbeam_data.log
DATAFILE=$WORKDIR/data/beam_data_hourly.csv

echo $(date)
/usr/bin/kinit -kt /var/kerberos/krb5/user/`id -u`/client.keytab ${USER}/cron/sbndgpvm01.fnal.gov@FNAL.GOV
klist
echo WORKDIR=$WORKDIR
echo WEBDATA=$WEBDATA

cd $WORKDIR
source venv/bin/activate
echo Run getHourlyData.py
./scripts/getHourlyData.py -o $DATAFILE >> $LOGFILE 2>&1

echo Copy data to web area
cp $DATAFILE $WEBDATA

