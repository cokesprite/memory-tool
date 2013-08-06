Memory logger/analysis tool

Version 1.0.0

Readme: How to use this tool for memory logger/analysis

1. Config environment
	a. This tool just for Linux OS，need to install python, matplotlib
	   $ sudo apt-get install python
	   $ sudo apt-get install python-matplotlib

2. Run tool
    a. Copy run.sh/do_parse.py to log file folder
	   $ cp run.sh /LOG_PATH/LOG1/        ex: cp run.sh /LOG_PATH/dlxp_memory_log_0514/
	   $ cp do_parse.py /LOG_PATH/LOG1/
	   
    b. Execute test script
       $ sh run.sh

3. Test result:
	When execute finish，folder /LOG_PATH/LOG1/ will generate below files automatically：
	   meminfo_analysis_a_group.png   >> For meminfo analysis(Group a): MemTotal + MemFree + Cached
	   Meminfo_analysis_b_group.png   >> For meminfo analysis(Group b): Buffers + Mlocked + AnonPages + Shmem + Slab + KernelStack + PageTables + VmallocAlloc + ION_Alloc
	   
	   procrank-parsed/  >> For procrank analysis result
	   procrank-parsed/csv-android.process.acore.csv      >> filter process android.process.acore into csc file
	   procrank-parsed/csv-android.process.acore.csv.png  >> generate graph automatically