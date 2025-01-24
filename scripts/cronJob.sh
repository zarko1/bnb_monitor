#!/bin/bash

WORKDIR=/exp/sbnd/app/users/${USER}/bnb_monitor/
WEBDATA=/web/sites/s/sbn-online.fnal.gov/htdocs/sbnd/beammon/data
LOGFILE=$WORKDIR/log/ifbeam_data.log
DATAFILE=$WORKDIR/data/beam_data_hourly.csv

echo $(date)
#export KRB5CCNAME=FILE:/tmp/krb5cc_`id -u`_cron$$
#/usr/bin/kinit -kt /var/kerberos/krb5/user/`id -u`/client.keytab ${USER}/cron/`hostname`@FNAL.GOV
klist
echo WORKDIR=$WORKDIR
echo WEBDATA=$WEBDATA

cd $WORKDIR
source venv/bin/activate
echo Run getHourlyData.py
./scripts/getHourlyData.py -o $DATAFILE >> $LOGFILE 2>&1

echo Copy data to web area
cp $DATAFILE $WEBDATA
