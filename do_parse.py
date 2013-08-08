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
    def __init__(self):
        self.path = sys.path[0] +'/'
        self.fileName = ''
        self.date = []
        self.memTotal = []
        self.memFree = []
        self.cached = []
        self.buffers = []
        self.mlocked = []
        self.anonPages = []
        self.shmem = []
        self.slab = []
        self.kernelStack = []
        self.pageTables = []
        self.vmallocAlloc = []
        self.ION_Alloc = []

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
        #plt.show
        
    def readData(self, logfile):
        self.file = logfile     
        input_file = open(self.file, "rb")
        spamreader = csv.reader(input_file)
        for row in spamreader:
            #if (row[1] != '' and row[2] !='' and row[10] !=''):
            self.date.append(row[0])
            self.memTotal.append(row[1])
            self.memFree.append(row[2])
            self.cached.append(row[10])
            self.buffers.append(row[9])
            self.mlocked.append(row[11])
            self.anonPages.append(row[12])
            self.shmem.append(row[13])
            self.slab.append(row[14])
            self.kernelStack.append(row[15])
            self.pageTables.append(row[16])
            self.vmallocAlloc.append(row[17])
            self.ION_Alloc.append(row[18])
        input_file.close()
        
        # Delete header: first column
        del self.date[0]
        del self.memFree[0]
        del self.memTotal[0]
        del self.cached[0]
        del self.buffers[0]
        del self.mlocked[0]
        del self.anonPages[0]
        del self.shmem[0]
        del self.slab[0]
        del self.kernelStack[0]
        del self.pageTables[0]
        del self.vmallocAlloc[0]
        del self.ION_Alloc[0]
        
        # KB -> MB
        self.date = self.formatDate(self.date)
        self.memTotal = self.formatValue(self.memTotal)
        self.memFree = self.formatValue(self.memFree)
        self.cached = self.formatValue(self.cached)
        self.buffers = self.formatValue(self.buffers)
        self.mlocked = self.formatValue(self.mlocked)
        self.anonPages = self.formatValue(self.anonPages)
        self.shmem = self.formatValue(self.shmem)
        self.slab = self.formatValue(self.slab)
        self.kernelStack = self.formatValue(self.kernelStack)
        self.pageTables = self.formatValue(self.pageTables)
        self.vmallocAlloc = self.formatValue(self.vmallocAlloc)
        self.ION_Alloc = self.formatValue(self.ION_Alloc)

    def parse_A_Group(self):
        N = len(self.date)
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return self.date[thisind]

        fig = plt.figure(dpi=100)
        fig.canvas.set_window_title('Meminfo analysis')
        ax = fig.add_subplot(111)
        ax.plot(ind,self.memTotal,'r-',self.memFree,'g-',self.cached,'c-')
        ax.grid(True)
        ax.set_title('Meminfo analysis -- ' + self.setPlotTitle(self.file))
        ax.set_xlabel('Time')
        ax.set_ylabel('Mem Info(MiB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        fig.autofmt_xdate()
        legend(('Total Mem','Free Mem','Cached'),0 )#'upper right'
        self.savePic('meminfo_analysis_a_group')


    def parse_B_Group(self):
        N = len(self.date)
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x+0.5), 0, N-1)
            return self.date[thisind]

        fig = plt.figure(dpi=100, figsize=(20, 20))
        fig.canvas.set_window_title('Meminfo analysis')

        ax = fig.add_subplot(211)
        ax.plot(ind,self.buffers,'g-',self.mlocked,'0.4', self.shmem,'c-',self.slab,'k-',self.kernelStack,'r-',self.pageTables,'y-',self.vmallocAlloc,'b-',self.ION_Alloc,'m-')
        ax.grid(True)
        ax.set_title('Meminfo analysis -- ' + self.setPlotTitle(self.file))
        ax.set_xlabel('Time')
        ax.set_ylabel('Mem Info(MiB)')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        fig.autofmt_xdate()
        legend(('Buffers','Mlocked','Shmem','Slab','KernelStack','PageTables','VmallocAlloc','ION_Alloc'),0 )

        ax1 = fig.add_subplot(212)
        ax1.plot(ind,self.anonPages,'g-',self.slab,'k-')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Mem Info(MiB)')
        ax1.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        #fig.autofmt_xdate()
        legend(('AnonPages', 'Slab'),'upper right')
        self.savePic('meminfo_analysis_b_group')

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


def parseMemInfo():
    meminfo = MemInfoParser()
    files = meminfo.findLogFile()
    for f in files:
        meminfo.readData(f)
        meminfo.parse_A_Group()
        meminfo.parse_B_Group()

def parseProcrank():
    p = ProcrankParser()
    csvfiles = p.findCsvFiles()
    for i in csvfiles:
        p.draw(i)

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm:p:")
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
        elif op == "-h":
            print "usage() func"
            #usage()
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
