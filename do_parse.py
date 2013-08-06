import sys, os
import sys, getopt
import os.path
import datetime
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.cbook as cbook
import matplotlib.ticker as ticker
import matplotlib.dates as dates

from pylab import plotfile, show, gca
from matplotlib.pyplot import plot,savefig,legend
from matplotlib.ticker import MultipleLocator, AutoLocator, FormatStrFormatter


class MemInfoParser:
    BGroup = ['Buffers', 'Mlocked', 'AnonPages','Shmem','Slab','KernelStack','PageTables','VmallocAlloc','ION_Alloc']

    def __init__(self):
        self.path = sys.path[0] +'/'

    def findLogFile(self):
        path = sys.path[0]
        #print path
        logfile = [item for item in os.listdir(path) if (item.endswith('.csv') and item[:7] =='memlog_')]
        return logfile

    def setPlotTitle(self,fileName):
        n = fileName[:-4]
        return n

    def formatDate(self,date):
        dateColumn = date
        #0517-01:05:10 -> 05/17 01:05
        fdate = []
        for dc in dateColumn:
            d = dc[:2]+"/"+dc[2:4]+" " + dc[-8:10]
            fdate.append(d)
        return fdate

    def formatValue(self,value):
        # KB -> MB
        kbs = value
        mbs = []
        for kb in kbs:
            mb = int(kb)/1000
            mbs.append(mb)
        return mbs

    def savePic(self, name='test'):
        n = name
        plt.savefig(n + '.png', dpi=200, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1)
        #plt.show()

    def parse_A_Group(self, logfile):
        #print logfile
        f = logfile
        input_file = open(f, "rb")

        date = []
        memTotal = []
        memFree = []
        cached = []
        #writer = csv.writer(file('new.csv', 'wb'))
        spamreader = csv.reader(input_file)
        for row in spamreader:
            if (row[1] != '' and row[2] !='' and row[10] !=''):
                date.append(row[0])
                memTotal.append(row[1])
                memFree.append(row[2])
                cached.append(row[10])
        input_file.close()
        del date[0]
        del memFree[0]
        del memTotal[0]
        del cached[0]

        date = self.formatDate(date)
        memTotal = self.formatValue(memTotal)
        memFree = self.formatValue(memFree)
        cached = self.formatValue(cached)
        N = len(date)
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return date[thisind]

        fig = plt.figure(dpi=100)
        fig.canvas.set_window_title('Meminfo analysis')
        ax = fig.add_subplot(111)
        ax.plot(ind,memTotal,'r-',memFree,'g-',cached,'c-')
        ax.grid(True)
        ax.set_title('Meminfo analysis -- ' + self.setPlotTitle(f))
        ax.set_xlabel('Time')
        ax.set_ylabel('Mem Info(MiB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        fig.autofmt_xdate()
        legend(('Total Mem','Free Mem','Cached'),0 )#'upper right'
        self.savePic('meminfo_analysis_a_group')

    def parse_AA_Group(self, logfile):
        print logfile
        datafile = logfile
        print ('loading %s' % datafile)
        r = mlab.csv2rec(datafile)

        N = len(r)
        ind = np.arange(N)
        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return r.time[thisind].strftime('%m-%d %H:%M:%S')

        fig = plt.figure(dpi=100, figsize=(15, 10))
        fig.canvas.set_window_title(logfile)
        ax = fig.add_subplot(111)
        ax.plot(ind, r.memtotal, 'g-', r.memfree, 'r-',r.cached, 'b-',)
        ax.grid(True)
        ax.set_title('MemoInfo analysis -- ' + self.setPlotTitle(datafile))
        ax.set_xlabel('Time')
        ax.set_ylabel('MemeInfo(kB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        fig.autofmt_xdate()

        legend(('MemTotal','MemFree','Cached'),0)
        self.savePic('meminfo_analysis_aa_group')

    def parse_B_Group(self, logfile):
        BGroup = ['Buffers', 'Mlocked', 'AnonPages','Shmem','Slab',
                  'KernelStack','PageTables','VmallocAlloc','ION_Alloc']
        f = logfile
        input_file = open(f, "rb")

        Buffers = []
        Mlocked = []
        AnonPages = []
        Shmem = []
        Slab = []
        KernelStack = []
        PageTables = []
        VmallocAlloc = []
        ION_Alloc = []

        for row in csv.reader(input_file):
            Buffers.append(row[9])
            Mlocked.append(row[11])
            AnonPages.append(row[12])
            Shmem.append(row[13])
            Slab.append(row[14])
            KernelStack.append(row[15])
            PageTables.append(row[16])
            VmallocAlloc.append(row[17])
            ION_Alloc.append(row[18])

        input_file.close()

        #for i in BGroup:
            #print i
            #del i[0]
        del Buffers[0]
        del Mlocked[0]
        del AnonPages[0]
        del Shmem[0]
        del Slab[0]
        del KernelStack[0]
        del PageTables[0]
        del VmallocAlloc[0]
        del ION_Alloc[0]

        N = len(Buffers)
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return r.time[thisind].strftime('%m-%d %H:%M:%S')

        fig = plt.figure(dpi=100, figsize=(20, 20))
        fig.canvas.set_window_title('Meminfo analysis')

        ax = fig.add_subplot(211)
        ax.plot(ind,Buffers,'g-',Mlocked,'0.4', Shmem,'c-',Slab,'k-',KernelStack,'r-',PageTables,'y-',VmallocAlloc,'b-',ION_Alloc,'m-')
        ax.grid(True)
        ax.set_title('Meminfo analysis -- ' + self.setPlotTitle(f))
        ax.set_xlabel('Count')
        ax.set_ylabel('Mem Info(kB)')
        fig.autofmt_xdate()

        legend(('Buffers','Mlocked','Shmem','Slab','KernelStack','PageTables','VmallocAlloc','ION_Alloc'),0 )#'upper right'

        ax1 = fig.add_subplot(212)
        ax1.plot(ind,AnonPages,'g-',Slab,'k-')
        legend(('AnonPages', 'Slab'),'upper right')
        self.savePic('meminfo_analysis_b_group')

    def parse_BB_Group(self, logfile):
        print logfile
        datafile = logfile
        print ('loading %s' % datafile)
        r = mlab.csv2rec(datafile)

        N = len(r)
        ind = np.arange(N)
        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return r.time[thisind].strftime('%m-%d %H:%M:%S')

        fig = plt.figure(dpi=100, figsize=(15, 20))
        fig.canvas.set_window_title(logfile)
        ax = fig.add_subplot(211)
        ax.plot(ind, r.buffers,'g-',r.shmem,'c-',r.slab,'k-',r.kernelstack,'r-',r.pagetables,'y-',r.vmallocalloc,'b-',r.ion_alloc,'m-')
        ax.grid(True)
        ax.set_title('MemoInfo analysis -- ' + self.setPlotTitle(datafile))
        ax.set_xlabel('Times')
        ax.set_ylabel('MemeInfo(kB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        fig.autofmt_xdate()
        legend(('Buffers','Shmem','Slab','KernelStack','PageTables','VmallocAlloc','ION_Alloc'),0 )#'upper right'

        ax = fig.add_subplot(212)
        ax.plot(ind,r.anonpages,'g-',r.slab,'k-')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        #fig.autofmt_xdate()
        legend(('AnonPages', 'Slab'),'upper right')
        self.savePic('meminfo_analysis_bb_group')

class ProcrankParser():
    def __init__(self):
        self.path = sys.path[0] +'/'+ 'procrank-parsed' + '/'

    def findCsvFiles(self):
        path = self.path
        csvfiles = [item for item in os.listdir(path) if item.endswith('.csv')]
        return csvfiles

    def setPlotTitle(self,fileName):
        name = fileName[4:]
        n = name[:-4]
        return n

    def draw(self,file):
        datafile = self.path + file
        print ('loading %s' % datafile)
        r = mlab.csv2rec(datafile)
        #r.sort()
        N = len(r)
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return r.count[thisind].strftime('%m-%d %H:%M:%S')

        fig = plt.figure(dpi=100, figsize=(15, 10))
        fig.canvas.set_window_title(file)
        ax = fig.add_subplot(111)
        ax.plot(ind, r.rss, 'g-', r.pss, 'r-',)
        ax.grid(True)
        ax.set_title('Procrank analysis -- ' + self.setPlotTitle(file), fontsize = 'medium')
        ax.set_xlabel('Time')
        ax.set_ylabel('Mem(kB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        legend(('RSS',"PSS"),0)
        fig.autofmt_xdate()

        plt.savefig(self.path + file  + '.png', dpi=200, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1)
        #plt.show()


def parseMemInfo():
    meminfo = MemInfoParser()
    files = meminfo.findLogFile()
    for f in files:
        meminfo.parse_A_Group(f)
        meminfo.parse_B_Group(f)
        # TBD: below function need to format csv file time-format and header-format
        #meminfo.parse_AA_Group(f)
        #meminfo.parse_BB_Group(f)

def parseProcrank():
    p = ProcrankParser()
    csvfiles = p.findCsvFiles()
    for i in csvfiles:
        #p.draw(i,0,'rss','pss')
        p.draw(i)

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:p:f:")
    except getopt.GetoptError, err:
        print str(err)
        #usage()
        sys.exit(2)
    for op, value in opts:
        if op == "-m":
            parseMemInfo()
            sys.exit(0)
        elif op == "-p":
            parseProcrank()
            sys.exit(0)
        elif op == "-f":
            fileProcrankFiles()
            sys.exit(0)
        elif op == "-h":
            print "usage() func"
            #usage()
            sys.exit(1)
    #if !opts:
    #    parseProcrank()

if __name__ == "__main__":
    main(sys.argv)
