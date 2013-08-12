Memory logger/analysis tool

Version 1.1.0

Readme: How to use this tool for memory logger/analysis

1. Config environment
	a. This tool just for Linux OS，need to install python, matplotlib
	   $ sudo apt-get install python
	   $ sudo apt-get install python-matplotlib

2. Run tool
    a. Copy run.sh/do_parse.py to log file folder
	   $ cp do_parse.py /LOG_PATH/LOG1/   ex: cp do_parse.py /LOG_PATH/dlxp_memory_log_0514/
	   
    b. Execute test script
       $ python do_parse.py -m 0     // meminfo analysis
	   $ python do_parse.py -p 0     // procrank analysis

3. Test result:
	When execute finish，folder /LOG_PATH/LOG1/ will generate below files automatically：
	   meminfo_analysis_a_group.png   >> For meminfo analysis(Group a): MemTotal + MemFree + Cached
	   Meminfo_analysis_b_group.png   >> For meminfo analysis(Group b): Buffers + Mlocked + AnonPages + Shmem + Slab + KernelStack + PageTables + VmallocAlloc + ION_Alloc
	   
	   procrank-parsed/  >> For procrank analysis result
	   procrank-parsed/csv-android.process.acore.csv      >> filter process android.process.acore into csc file
	   procrank-parsed/csv-android.process.acore.csv.png  >> generate graph automatically
	   
	   
	   
**************************************************************************************************************
	   
1. Meminfo
	Meminfo log file helps to collect system-wide memory information, which is always recorded during 
	system is running. Meminfo contains information like total memory, free memory, cached memory and 
	others. When memory leakage happens, it is expected to show the memory data-changing trend.
	
2. Procrank
	Procrank log file shows application memory usage (RSS and PSS) ranking in periodic. Compare with meminfo, 
	it is detailed information to detect which application may cause memory leakage.
	
3. Kmemleak
	Kmemleak is a tool to detect suspicious memory leakage in kernel. From the kmemleak log file, it is 
	expected to find most frequent occurrence of suspicious call stack.
	
	
Analysis Method and Tool

	Firstly, parse all meminfo in log file. And generate the curves of each entry of meminfo. From the curve, 
it is expected to get the overview determine whether there is system-wide memory leakage, according to the 
meminfo entry’s increment trend.

	Generate kmemleak statistics, and then get the most frequently occurred entries for further analysis.
	
	Generate process list and their memory usage (RSS/PSS) curves to determine abnormal ones. This analysis 
should be operated on those specified process like Launcher, system_server, acore etc.

	An automation tool is being developed to generate all above information and curve charts. It is expected 
to be flexible to add more memory log entries for further analysis. This memory tool is developed with python 
and matplotlib.

	Currently, this memory tool includes a bash script and a python script. In bash script, some text-processing 
commands are used to collect all memory information with special format. And the python script is used to load 
formatted data to output curve charts.

run.sh
do_parse.py

********************************************************************************************************************
