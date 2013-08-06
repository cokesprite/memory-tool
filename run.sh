#!/bin/bash

#for i in $(find . -name procrank.txt)
# assume file is located in ./DUT107/htclog/sd_htclog/procrank.txt
# need to set "htclog/sd_htclog" as PATH prefix

#for i in $1
for i in $(find . -name *_procrank.txt)

do
path=${i%/log*}
path=${path#*/}
echo $path
#mkdir script-$path
#pushd script-$path

mkdir procrank-parsed
#pushd procrank-parsed
cd procrank-parsed

for proc in com.htc.launcher surfaceflinger system_server com.android.browser android.process.acore com.android.phone com.android.systemui com.htc.idlescreen.shortcut com.android.chrome com.android.htcdialer com.htc.android.htcime
do
	echo Now processing $proc
	cat ../$i |grep -e "PROCRANK" |sed 's/^.*(\(.*\)).*$/\1/' > count-$proc.txt
	cat count-$proc.txt |sed 's/ /#/g' > time-$proc.txt
	cat ../$i |grep -e "$proc$" -e CST > time_and_$proc
	#cat time_and_$proc |grep CST |sed 's/ /-/g' > time-$proc.txt
	cat time_and_$proc |grep $proc |awk '{print $3, $4}'|sed 's/K//g' > PSS-RSS-$proc.txt
    time_count=`wc -l time-$proc.txt | awk '{print $1}'`
	echo time count = `wc -l time-$proc.txt`
    pss_count=`wc -l PSS-RSS-$proc.txt | awk '{print $1}'`
	echo PSS count = `wc -l PSS-RSS-$proc.txt`
	echo Count RSS PSS > result-$proc.txt
    if [ "$time_count" != "$pss_count" ]
    then
        head -$pss_count time-$proc.txt > time2-$proc.txt
    fi
	paste time2-$proc.txt PSS-RSS-$proc.txt >> result-$proc.txt	
	cat result-$proc.txt |sed 's/ /\t/g' > tab-result-$proc.txt
	cat tab-result-$proc.txt |sed -n 's/\t/,/gp' > c-$proc.txt
	cat c-$proc.txt |sed 's/\#/ /g' > csv-$proc.csv
	
	# Delete all temp files
	rm count-$proc.txt
	rm time_and_$proc
	rm time-$proc.txt
	rm PSS-RSS-$proc.txt
	rm time2-$proc.txt
	rm result-$proc.txt
	rm tab-result-$proc.txt
	rm c-$proc.txt
	
done

pwd
cd ../

#-p: parse procrank csv file, and generate graph automatically. 
# 0: default value, not useful
python do_parse.py -p 0

#-m: parse meminfo csv file, and generate graph automatically. 
# 0: default value, not useful
python do_parse.py -m 0

#pwd
#popd
pwd
done
