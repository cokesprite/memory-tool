import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from matplotlib.pyplot import plot,savefig,legend

class Procrank(object):
    def __init__(self, filePath):
        self.procrank = {}
        self.pssAverage = {}
        self.rssAverage = {}
        self.pssPeak = {}
        self.rssPeak = {}
        self.filePath = filePath
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        chunks = fileObject.split('------ PROCRANK')
        for chunk in chunks[1:]:
            lines = chunk.split('\n')
            date = re.search('\d\d-\d\d \d\d:\d\d:\d\d', lines[0])
            date = date.group()
            for line in lines[2:-5]:
                formated = line.split()
                if self.procrank.has_key(formated[-1]):
                    proc = self.procrank[formated[-1]]
                    proc.append(formated[1:-1] + [date])
                    self.procrank[formated[-1]] = proc
                else:
                    self.procrank[formated[-1]] = [formated[1:-1] + [date]]
        for key in self.procrank.keys():
            pAverage = 0
            pPeak = 0
            rAverage = 0
            rPeak = 0
            values = self.procrank[key]
            for value in values:
                pAverage = pAverage + int(value[2][:-1]) # value[2] is Pss, [:-1] remove tailed 'K'
                if pPeak < int(value[2][:-1]):
                    pPeak = int(value[2][:-1])
                rAverage = rAverage + int(value[1][:-1]) # value[1] is Rss, [:-1] remove tailed 'K'
                if rPeak < int(value[1][:-1]):
                    rPeak = int(value[1][:-1])
            pAverage = pAverage / len(values)
            rAverage = rAverage / len(values)
            self.pssAverage[key] = pAverage
            self.pssPeak[key] = pPeak
            self.rssAverage[key] = rAverage
            self.rssPeak[key] = rPeak

    def topProcs(self):
        procs = []
        sortedAverage = sorted(self.pssAverage.iteritems(), key=lambda (k,v): (v,k), reverse=True)
        for proc in sortedAverage[:20]:
            procs.append(proc[0])
        return procs

    def hotProcs(self):
        return ['com.htc.launcher', 'surfaceflinger', 'system_server', 'com.android.browser', 'android.process.acore',
                'com.android.phone', 'com.android.systemui', 'com.htc.idlescreen.shortcut', 'com.android.chrome',
                'com.android.launcher', 'com.android.htcdialer', 'com.htc.android.htcime']

    def getProcRecords(self, proc):
        vss = []
        rss = []
        pss = []
        uss = []
        date = []
        if self.procrank.has_key(proc):
            records = self.procrank[proc]
            for record in records:
                vss.append(record[0][:-1])
                rss.append(record[1][:-1])
                pss.append(record[2][:-1])
                uss.append(record[3][:-1])
                date.append(record[4][:-3])
        else:
            print 'Error! There is no such process.'
        return (vss, rss, pss, uss, date)

    def draw(self, proc):
        if self.procrank.has_key(proc):
            (vss, rss, pss, uss, date) = self.getProcRecords(proc)
            d = date
            r = rss
            p = pss
            N = len(d)
            ind = np.arange(N)

            def format_date(x, pos = None):
                thisind = np.clip(int(x + 0.5), 0, N - 1)
                return d[thisind]

            fig = plt.figure(dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(ind, r, 'g-', p, 'r-',)
            ax.grid(True)
            ax.set_title('Procrank analysis -- ' + proc, fontsize='large')
            ax.set_xlabel('Time')
            ax.set_ylabel('Mem(kB)')
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
            legend(('RSS',"PSS"),0)
            fig.autofmt_xdate()
            print 'heihei'
            plt.savefig('./' + proc + '.png', dpi=200, facecolor='w', edgecolor='w',
                    orientation='portrait', papertype=None, format=None,
                    transparent=False, bbox_inches=None, pad_inches=0.1)

def _Main():
    procrank = Procrank('procrank')
    for proc in procrank.topProcs():
        procrank.draw(proc)
    for proc in procrank.hotProcs():
        procrank.draw(proc)

if __name__ == '__main__':
    _Main()
