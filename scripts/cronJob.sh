#!/bin/bash

WORKDIR=/exp/sbnd/app/users/zarko/work/bnbmon/
WEBDATA=/publicweb/z/zarko/bnb_monitor/data
LOGFILE=$WORKDIR/log/ifbeam_data.log
DATAFILE=$WORKDIR/data/beam_data_hourly.csv

echo $(date)
echo WORKDIR=$WORKDIR
echo WEBDATA=$WEBDATA

cd $WORKDIR
source venv/bin/activate
echo Run getHourlyData.py
./scripts/getHourlyData.py -o $DATAFILE >> $LOGFILE 2>&1

echo Copy data to web area
cp $DATAFILE $WEBDATA

