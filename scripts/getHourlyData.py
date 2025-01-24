#!/usr/bin/env python

from os.path import isfile
from datetime import timedelta, date,datetime
import sys
from urllib.request import urlopen
import pandas as pd
import numpy as np
from scipy import integrate
from functools import reduce
import io
import argparse

def hours(start_time, end_time):
    current_time = start_time+timedelta(hours=1)
    while current_time <= end_time:
        yield current_time
        current_time += timedelta(hours=1)

def fill_zero(tstamp, devlist):
    output="%s,"%(tstamp)
    output+="0,"*len(savedev)
    output+="1,"*len(savedev) #IFBEAM efficiency, take as 1 when beam is down
    output+="0,0,0,0," # spills,triggers,fom and uptime
    output+="0,0,0\n" # fail tor, horn, fom
    return output

def beam_quality(devdict):
    #give each device 2 bits
    #00 -all good
    #01 - no data
    #10 - under cut
    #11 - over cut

    #check pot; will count only out of bounds values and nans, if there is no beam just return no error
    if abs(devdict["E:TOR860"])<0.5:
        return bdqnorm
    err=0b0
    for d in devs_used_for_bdq:
        if devdict[d]>devlimits[d]["max"]:
            err=err | 0b11
        elif devdict[d]<devlimits[d]["min"]:
            err=err | 0b10
        elif np.isnan(devdict[d]):
            err=err | 0b01
        err=err<<2
    err=err>>2
    return bdqnorm|err

def get_fom(data,bpm_zpos,bpm_off,tgt_zpos,norm):
    #check if we have all the data
    for d in devs_used_for_fom:
        if np.isnan(data[d]):
            #print("missing data")
            #print(data)
            return float("nan")
    #estimate FOM from BPMs
  
    xy={}
    for d in devs_used_for_fom:
        xy[d]=data[d]-bpm_off[d]

    xpos=xy["E:HP875"]+(xy["E:HPTG1"]-xy["E:HP875"])/(bpm_zpos["E:HPTG1"]-bpm_zpos["E:HP875"])*(tgt_zpos["cnt"]-bpm_zpos["E:HP875"])
    ypos=xy["E:VP873"]+(xy["E:VP875"]-xy["E:VP873"])/(bpm_zpos["E:VP875"]-bpm_zpos["E:VP873"])*(tgt_zpos["cnt"]-bpm_zpos["E:VP873"])
    res=norm
    if xpos>1 or ypos>1:
        res, err=integrate.dblquad(gaussian_2d, -5.1, 5.1, cmy, cpy, (xpos,ypos,1,1),epsabs=0.0001)
    #print (xpos,ypos,np.sqrt(xpos*xpos+ypos*ypos),res/norm)
    return min(res/norm,1)

def gaussian_2d(y, x, mu_x, mu_y, sigma_x, sigma_y):
    exponent = -((x - mu_x)**2 / (2 * sigma_x**2) + (y - mu_y)**2 / (2 * sigma_y**2))
    result=np.exp(exponent) / (2 * np.pi * sigma_x * sigma_y)
    return result

def cpy(x):
    tgt_r=5.1
    return np.sqrt(tgt_r*tgt_r-(tgt_r-abs(x))*(tgt_r-abs(x)))

def cmy(x):
    return -cpy(x)


parser = argparse.ArgumentParser(
                    prog='getHourlyData.py',
                    description='Get beam data, bin it hourly, and store it in csv file for bnb monitor web page.',
                    epilog='Contact: zarko@fnal.gov')
parser.add_argument('-o', '--output-file', help='Ouptut csv file.')
parser.add_argument('-s', '--start-date', help='Starting from this date. Used only when starting new file, otherwise just appending to existing date. Should be in format YYYY-MM-DD, like 2024-12-09.')
parser.add_argument('-d', '--debug', action='store_true', help='Prints out more info.')

args = parser.parse_args()

bundle="BNB_monitor"
savedev=["E:TOR860","E:TOR875","E:THCURR","E:LHCURR","E:LM875A","E:LM875B","E:LM875C","E:HP873","E:VP873","E:HP875","E:VP875","E:HPTG1","E:VPTG1","E:HPTG2","E:VPTG2"]

devlimits={
    "E:TOR860": { "min": -0.5,
                  "max": 6},
    "E:TOR875": { "min": -0.5,
                  "max": 6},
    "E:THCURR": { "min": 172,
                  "max": 174},
    "E:HP875": { "min": -6-0.5,
                  "max": -6+0.5},
    "E:HPTG1": { "min": -2-0.5,
                  "max": -2+0.5},
    "E:VP875": { "min": -0.75-0.5,
                 "max": -0.75+0.5},
    "E:VP873": { "min": 2.8-0.5,
                 "max": 2.8+0.5},
    "FOM": { "min": 0.95,
             "max": 1}
    }
devs_used_for_bdq=["E:TOR860","E:THCURR","FOM"]
devs_used_for_fom=["E:VP873","E:HP875","E:VP875","E:HPTG1"]
bpm_zpos={"E:VP873": 191.153656,
          "E:HP875": 202.116104,
          "E:VP875": 202.3193205,
          "E:HPTG1": 204.833267,
          "E:VPTG1": 204.629608,
          "E:HPTG2": 205.240662,
          "E:VPTG2": 205.036835}
#target is a cylinder 71.1 cm long and 0.51 cm in radiu
tgt_zpos={"beg": 206.870895-0.711/2,
          "cnt": 206.870895,
          "end": 206.870895+0.711/2}
tgt_r=0.51

bdqnorm=0b1
for d in devs_used_for_bdq:
    bdqnorm=bdqnorm<<2

output_file="output.csv"
start_time=datetime(2024,12,9,0,0,0) #Monday before beam came back
debug=args.debug

if args.output_file is not None:
    output_file=args.output_file
if args.start_date is not None:
    start_time=datetime.strptime(args.start_date,"%Y-%m-%d")

end_time=datetime(datetime.now().year,datetime.now().month,datetime.now().day,datetime.now().hour,0,0)

if isfile(output_file):
    tmpfile=open(output_file,'r')
    for ln in tmpfile:
        if "Time" not in ln:
            start_time=datetime.strptime(ln.split(",")[0],"%Y-%m-%dT%H:%M:%S")
    tmpfile.close
else:
    outfile=open(output_file,'w')    
    #Add header
    header="Time,"+",".join(savedev)+","+",".join(["%s Efficiency"%s for s in savedev])
    header+=",NSpills,NTriggers,FOM,Uptime"
    for d in devs_used_for_bdq:
        header+=",Fail %s"%d
    header+="\n"
    outfile.write(header)
    outfile.close()

print("Output file: ",output_file)
print("Start date: ",start_time.isoformat())
print("End date: ",end_time.isoformat())
#take norm as 1mm beam on target center
norm, err=integrate.dblquad(gaussian_2d, -5.1, 5.1, cmy, cpy, (0,0,1,1)) 

t0=start_time
outfile=open(output_file,'a')

for time_slice in hours(start_time, end_time):
    #first get the nominal positions for BPMs. it changes very rarely, so don't need to
    #check multiple times during the hour. it is logged every 15m
    url="https://dbweb9.fnal.gov:8443/ifbeam/data/data?b=BNB_BPM_settings&t0=%s&t1=%s&f=csv"%(t0.isoformat(),(t0+timedelta(minutes=15)).isoformat())
    response = urlopen(url).read().decode()
    bpm_off={}
    for l in response.split("\n"):
        data=l.split(",")
        if "timestamp" in l or len(l)<4:
            continue
        bpm_off[data[1].replace("_",":").strip("S")]=np.float64(data[3])

    t1=time_slice
    url="https://dbdata0vm.fnal.gov:8104/ifbeam/data/data?b=%s&t0=%s&t1=%s&f=csv"%(bundle,t0.isoformat(),t1.isoformat())
    if debug:
        print(url)
    gotit=False
    itry=0
    while not gotit and itry<10:
        try:
            response = urlopen(url).read().decode()
            gotit=True
        except Exception as e:
            itry+=1
            print("Failed ",itry,e)
    if not gotit:
        print("Failed to get beam data %i times. Giving up."%itry)
        sys.exit(1)

    if debug:
        print("Got data after %i retries."%itry)
              
    df=pd.read_csv(io.StringIO(response))
    
    #drop L:LNDMPE it has bad timestamps throwing everything off
    df=df[df.name!="L:LNDMPE"]

    #remove data outside of time boundaries (ifbeam returns with some padding)
    df=df[(df["timestamp"]>t0.timestamp()*1000)&(df["timestamp"]<t1.timestamp()*1000)]

    #fill 0s if dataframe is empty
    if len(df)<2:
        output=fill_zero(t1.isoformat(),savedev)
        t0=time_slice
        outfile.write(output)
        continue

    #align on time and put each device into a column
    devlist=df.name.unique()
    dflist=[]
    for dev in devlist:
        dfdev=df[df.name==dev][["timestamp","value(s)"]]
        dfdev.rename(columns={"value(s)":dev},inplace=True)
        dflist.append(dfdev)
    ddf=reduce(lambda left,right: pd.merge_asof(left,right, on=['timestamp'], direction='nearest',tolerance=10),dflist)
    
    #select spills with beam
    selection_tor860=[]
    selection_tor875=[]
    if "E:TOR860" in devlist:
        selection_tor860=(ddf["E:TOR860"]>0.1)&(ddf["E:TOR860"]<6)
    if "E:TOR875" in devlist:
        selection_tor875=(ddf["E:TOR875"]>0.1)&(ddf["E:TOR875"]<6)
        
    if np.count_nonzero(selection_tor860)==0 and np.count_nonzero(selection_tor875)==0:
        #no toroids in event, so count as 0
        output=fill_zero(t1.isoformat(),savedev)
        t0=time_slice
        if debug:
            print("No toroids in events")
            print(output)
        outfile.write(output)
        continue
    
    #looks like there was some beam, so can do beam quality cuts
    ddf["FOM"]=ddf.apply(lambda x: get_fom({d:x[d] for d in devs_used_for_fom},bpm_zpos,bpm_off,tgt_zpos,norm),axis=1)
    ddf["BDQ"]=ddf.apply(lambda x: beam_quality({ d:x[d] for d in devs_used_for_bdq}), axis=1)
    
    mask=0b11
    for d in devs_used_for_bdq[::-1]:
        ddf["Fail %s"%d]  = ddf.apply(lambda x: bool(int(x["BDQ"])&mask),axis=1)
        mask=mask<<2
    
    if np.count_nonzero(selection_tor860)>np.count_nonzero(selection_tor875):
        selection=selection_tor860
    else:
        selection=selection_tor875

    if np.count_nonzero(selection_tor860)>0:
        if abs(np.count_nonzero(selection_tor875)/np.count_nonzero(selection_tor860)-1)>0.005:
            print("%s Mismatch between tor860 and tor875 counts. %f vs %f"%(t0.isoformat(),np.count_nonzero(selection_tor860),np.count_nonzero(selection_tor875)))

    N_spills=len(ddf[selection]) # with beam
    N_triggers=ddf["E:TOR860"].count() # total triggers
    #use E1DCNT for expected number of triggers if possible. unless it rewinds
    if "E:1DCNT" in devlist:
        if ddf["E:1DCNT"].dropna().iloc[-1]>ddf["E:1DCNT"].dropna().iloc[0]:
            N=ddf["E:1DCNT"].dropna().iloc[-1] - ddf["E:1DCNT"].dropna().iloc[0]+1
            if N_spills>0:
                if abs((N-len(ddf[~selection]["E:1DCNT"]))/float(N_spills)-1)>0.005:
                    print("%s Events not adding up!"%t0.isoformat())
                    print("\tN_spills: ",N_spills)
                    print("\tN_triggers: ",N_triggers)
                    print("\t1D count: ",N)
                    print("\tNo beam spills: ",len(ddf[~selection]["E:1DCNT"]))
            if N>N_triggers:
                N_triggers=N


    #fill zeros if no beam
    if N_spills==0:
        output=fill_zero(t1.isoformat(),savedev)
        t0=time_slice
        if debug:
            print("N_spills=0")
            print(output)
        outfile.write(output)
        continue

    #process data with beam
    tot={}
    N={}
    output=t1.isoformat()+","
    for dev in savedev:
        if dev in devlist:
            tot[dev]=ddf[selection][dev].sum()
            output+="%f,"%(tot[dev]/float(N_spills))
        else:
            output+="-999," # no data for this device
    for dev in savedev:
        if dev in devlist:
            if dev=="E:TOR860" or dev=="E:TOR875":
                #toroids save on every trigger, so estimate efficiency based on all saved data
                N[dev]=len(ddf[dev].dropna())
                output+="%4.3f,"%(N[dev]/float(N_triggers))
            else:
                #other devices like BPMs aren't necessarily stored when there is no beam
                #take efficiency relative to toroids
                N[dev]=len(ddf[selection][dev].dropna())
                output+="%4.3f,"%(N[dev]/float(N_spills))
        else:
            output+="-1," # no data for this device
    output+="%i,%i"%(N_spills,N_triggers) #store N_selected so I can get total delivered POT 
    #add FOM
    output+=",%4.2f"%(ddf[selection]["FOM"].dropna().mean())
    
    #check uptime
    #take 1min bins and count as beam up if there was any beam during that minute
    bins=np.linspace(t0.timestamp()*1000,t1.timestamp()*1000,num=60)
    ddf["time_bin"] = pd.cut(ddf["timestamp"], bins=bins)
    uptime=len(ddf[selection]["time_bin"].unique())/60.
    
    output+=",%4.2f"%(uptime)
    for d in devs_used_for_bdq:
        output+=",%i"%(ddf["Fail %s"%d].sum())
    output+="\n"
    
    if debug:
        print(output)
    outfile.write(output)
    t0=time_slice

outfile.close()



