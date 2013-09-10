import re
import os
import sys
import time
import datetime
import optparse
import numpy as np

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors, fonts
from reportlab.graphics.charts.axes import XValueAxis
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus.tables import TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf'))
    fonts.addMapping('Arial', 0, 0, 'Arial')
    fonts.addMapping('Arial', 0, 1, 'Arial')
    Bullet = True
except:
    Bullet = False

(PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
Styles = {'Normal': ParagraphStyle(name = 'Normal', fontName = 'Helvetica', fontSize = 10, leading = 12, spaceAfter = 5, bulletFontName = 'Arial' if Bullet else 'Helvetica', bulletFontSize = 10),
          'Tips': ParagraphStyle(name = 'Tips', fontName = 'Helvetica', fontSize = 8, leading = 12),
          'Heading1': ParagraphStyle(name = 'Heading1', fontName = 'Helvetica-Bold', fontSize = 20, leading = 22, spaceBefore = 30, spaceAfter = 30),
          'Heading2': ParagraphStyle(name = 'Heading2', fontName = 'Helvetica', fontSize = 14, leading = 12, spaceBefore = 20, spaceAfter = 20), }

PATTERN = {"adreno_start": "DISPLAY", "kgsl_open": "DISPLAY", "kgsl_ioctl": "DISPLAY", "wifi": "WIFI", "ipv6_setsockopt": "NETWORK", "vid_dec_open": "VIDEO"}

class Meminfo(object):
    Free = {'MemFree': 1, 'Cached': 1, 'SwapCached': 1, 'Mlocked': -1, 'Shmem': -1}
    Used = ['AnonPages', 'Slab', 'VmallocAlloc', 'Mlocked', 'Shmem', 'KernelStack', 'PageTables', 'KGSL_ALLOC', 'ION_ALLOC', 'ION_Alloc']
    SwapUsage = {'SwapTotal': 1, 'SwapFree': -1}
    LMKFile = {'Cached': 1, 'Buffers': 1, 'SwapCached': 1, 'Mlocked': -1, 'Shmem': -1}
    Items = ['MemTotal', 'MemFree', 'Buffers', 'Cached', 'SwapCached', 'Active', 'Inactive', 'Active(anon)', 'Inactive(anon)', 'Active(file)', 'Inactive(file)', 'Unevictable', 'Mlocked', 'HighTotal', 'HighFree', 'LowTotal', 'LowFree', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback', 'AnonPages', 'Mapped', 'Shmem', 'Slab', 'SReclaimable', 'SUnreclaim', 'KernelStack', 'PageTables', 'NFS_Unstable', 'Bounce', 'WritebackTmp', 'CommitLimit', 'Committed_AS', 'VmallocTotal', 'VmallocUsed', 'VmallocIoRemap', 'VmallocAlloc', 'VmallocMap', 'VmallocUserMap', 'VmallocVpage', 'VmallocChunk', 'KGSL_ALLOC', 'ION_ALLOC']
    Summary = ['Free', 'MemFree', 'Cached', 'SwapCached', 'Used', 'AnonPages', 'Slab', 'Buffers', 'Mlocked', 'Shmem', 'KernelStack', 'PageTables', 'VmallocAlloc', 'KGSL_ALLOC', 'ION_Alloc', 'ION_ALLOC', 'SwapUsage', 'LMK File']

    def __init__(self, filePath):
        self.meminfo = {}
        self.filePath = filePath
        self.ram = 0
        self._parse()

    def _parse(self):
        print '---> Start parsing meminfo memlog ...'
        try:
            fileObject = open(self.filePath, 'r').read()
        except:
            print '---> ERROR: THERE IS NO MEMINFO MEMLOG!'
            sys.exit(1)
        chunks = fileObject.split('------ MEMORY INFO')
        dates = []
        self.meminfo['Free'] = []
        self.meminfo['Used'] = []
        self.meminfo['LMK File'] = []
        for chunk in chunks[1:]:
            lines = chunk.split('\n')
            date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0]).group()
            dates.append(date)
            start = False
            for line in lines:
                if not start:
                    if re.match('MemTotal', line) == None:
                        continue
                    else:
                        start = True
                formated = line.split()
                if len(formated) == 0: break
                if not self.meminfo.has_key(formated[0][:-1]):
                    self.meminfo[formated[0][:-1]] = []
                self.meminfo[formated[0][:-1]].append([formated[1], date])
                if formated[0][:-1] == 'MemTotal' and self.ram == 0:
                    self.ram = int(formated[1])
            self.meminfo['Free'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) * self.Free[value] for value in filter(lambda x: self.meminfo.has_key(x), self.Free.keys())]), date])
            self.meminfo['Used'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) for value in filter(lambda x: self.meminfo.has_key(x), self.Used)]), date])
            if set(self.meminfo.keys()) & set(self.SwapUsage.keys()):
                if not self.meminfo.has_key('SwapUsage'): self.meminfo['SwapUsage'] = []
                self.meminfo['SwapUsage'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) * self.SwapUsage[value] for value in filter(lambda x: self.meminfo.has_key(x), self.SwapUsage.keys())]), date])
            if set(self.meminfo.keys()) & set(self.LMKFile.keys()):
                if not self.meminfo.has_key('LMK File'): self.meminfo['LMK File'] = []
                self.meminfo['LMK File'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) * self.LMKFile[value] for value in filter(lambda x: self.meminfo.has_key(x), self.LMKFile.keys())]), date])
        print '---> Done'

    def tableData(self, items):
        return [['Item', 'Average (MB)', 'Peak (MB)']] + [[item,
                '%.1f' % ((reduce(lambda x, y: x + y, [int(value[0]) for value in self.meminfo[item]]) / len(self.meminfo[item])) / 1000.0),
                '%.1f' % (max([int(value[0]) for value in self.meminfo[item]]) / 1000.0)] for item in filter(lambda x: self.meminfo.has_key(x), items)]

    def drawingData(self, items, title=None):
        data = []
        for item in filter(lambda x: self.meminfo.has_key(x), items):
            dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[1] for value in self.meminfo[item]])
            data.append(zip(dates, [int(value[0]) for value in self.meminfo[item]]))
        return (items, dates[0], dates[-1], data, title)

    def overRange(self, items, rangeValue):
        return filter(lambda x: max([int(value[0]) for value in self.meminfo[x]]) > rangeValue, filter(lambda x: self.meminfo.has_key(x), items))

    def inRange(self, items, rangeValue):
        return filter(lambda x: max([int(value[0]) for value in self.meminfo[x]]) < rangeValue, filter(lambda x: self.meminfo.has_key(x), items))

    def hasLeakage(self, item):
        def var(X):
            S = 0.0
            SS = 0.0
            for x in X:
                S += x
                SS += x*x
            xbar = S/float(len(X))
            return (SS - len(X) * xbar * xbar) / (len(X) -1.0)
        def cov(X,Y):
            n = len(X)
            xbar = sum(X) / n
            ybar = sum(Y) / n
            return sum([(x-xbar)*(y-ybar) for x,y in zip(X,Y)])/(n-1)
        def beta(x,y):
            return cov(x,y)/var(x)
        if self.meminfo.has_key(item):
            converted = map(lambda tstring: [int(tstring[0]), time.mktime(time.strptime(tstring[1], "%Y-%m-%d %H:%M:%S"))], self.meminfo[item])
            arr = np.array(converted)
            start = int(arr[:,1][0])
            end = int(arr[:,1][-1])
            split = 10
            continious = 0
            for index in range(start, end, 3600):
                conditions = (arr[:,1] >= index) & (arr[:,1] <= (index + 3600))
                subArray = arr[:,0].compress(conditions)
                windows = np.array_split(subArray, split)
                count = 0
                for i in range(len(windows)):
                    y = windows[i].tolist()
                    if len(y) <= 1: continue
                    x = range(1, len(y) + 1)
                    increase = beta(x, y)
                    if increase > 1: count = count +1
                    else: count = 0
                    if count >= 4:
                        continious = continious + 1
                        break
                if count < 4: continious = 0
                if continious >= 5: return True
        return False

    def hasMoreLeakage(self, item):
        def var(X):
            S = 0.0
            SS = 0.0
            for x in X:
                S += x
                SS += x*x
            xbar = S/float(len(X))
            return (SS - len(X) * xbar * xbar) / (len(X) -1.0)
        def cov(X,Y):
            n = len(X)
            xbar = sum(X) / n
            ybar = sum(Y) / n
            return sum([(x-xbar)*(y-ybar) for x,y in zip(X,Y)])/(n-1)
        def beta(x,y):
            return cov(x,y)/var(x)

        if self.meminfo.has_key(item):
            arr = np.array(self.meminfo[item])
            percentage = []
            for splits in range(3, 10, 1):
                subArrs = np.array_split(arr, splits)
                count = 0
                for i in range(splits):
                    values = subArrs[i][:,0].astype(np.int)
                    mean = values.mean()
                    if values[-1] > mean and values[0] < mean:
                        count = count + 1
                percentage.append(int(float(count) * 100 / splits))
            y = arr[:,0].astype(np.int).tolist()
            x = range(1, len(y) + 1)
            beta = beta(x, y)
            if beta > 1:
                return (beta, sum(percentage) / len(percentage))
            else:
                return False

class Procrank(object):
    RAMS = {512: ((20, 50, 200), (2, 5, 20)), 768: ((20, 50, 200), (2, 5, 20)), 1024: ((50, 100, 500), (5, 10, 50)), 2048: ((50, 100, 500), (5, 10, 50))}
    def __init__(self, filePath):
        self.procrank = {}
        self.dates = []
        self.ram = 0
        self.filePath = filePath
        self._parse()

    def _parse(self):
        print '---> Start parsing procrank memlog ...'
        try:
            fileObject = open(self.filePath, 'r').read()
            chunks = fileObject.split('------ PROCRANK')
            for chunk in chunks[1:]:
                lines = chunk.split('\n')
                date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0]).group()
                self.dates.append(date)
                ram = re.search("(?<=RAM: )\d+(?=K)", lines[-2])
                if ram != None and self.ram == 0:
                    self.ram = reduce(lambda x, y: y if x <= (int(ram.group()) / 1000) and y > (int(ram.group()) / 1000) else x, self.RAMS.keys())
                start = False
                for line in lines:
                    if not start:
                        if re.search("^\s*\d+(\s+\d+K){4}", line) != None: start = True
                        else: continue
                    else:
                        if re.search("^\s*\d+(\s+\d+K){4}", line) == None:
                            start = False
                            break
                    formated = line.split()
                    if not self.procrank.has_key(formated[-1]):
                        self.procrank[formated[-1]] = []
                    self.procrank[formated[-1]].append(formated[1:-1] + [date])
            print '---> Done'
        except:
            print '---> WARNING: THERE IS NO PROCRANK MEMLOG!'

    def topProcs(self):
        return sorted(self.procrank.keys(), key=lambda proc: reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]), reverse=True)[:20]

    def peakHighProcs(self):
        return sorted(filter(lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]) >= 1000 * self.RAMS[self.ram][0][1], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)

    def peakMediumProcs(self):
        return sorted(filter(lambda proc: 1000 * self.RAMS[self.ram][0][0] <= max([int(value[2][:-1]) for value in self.procrank[proc]]) < 1000 * self.RAMS[self.ram][0][1], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)

    def peakLowProcs(self):
        return sorted(filter(lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]) < 1000 * self.RAMS[self.ram][0][0], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)[:10]

    def hotProcs(self):
        return filter(lambda x: self.procrank.has_key(x), ['com.htc.launcher', 'surfaceflinger', 'system_server', 'com.android.browser', 'android.process.acore', 'com.android.phone', 'com.android.systemui', 'com.htc.idlescreen.shortcut', 'com.android.chrome', 'com.android.launcher', 'com.android.htcdialer', 'com.htc.android.htcime'])

    def tableData(self, procs):
        return [['Process Name', 'PSS Average (MB)', 'PSS Peak (MB)']] + [[proc,
                '%.1f' % ((reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc])) / 1000.0),
                '%.1f' % (max([int(value[2][:-1]) for value in self.procrank[proc]]) / 1000.0)] for proc in procs]

    def drawingData(self, procs, title=None):
        data = []
        fullDates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), self.dates)
        for proc in procs:
            dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[4] for value in self.procrank[proc]])
            data.append(sorted(zip(dates, [int(value[2][:-1]) for value in self.procrank[proc]]) + [(left, 0) for left in (set(fullDates) - set(dates))], key=lambda (x, y): x, reverse=True))
        return (procs, fullDates[0], fullDates[-1], data, title)

class EventsLog(object):
    def __init__(self, filePaths):
        self.filePaths = filePaths
        self.anr = {}
        self._parse()

    def _parse(self):
        print '---> Start parsing event logs...'
        for filePath in self.filePaths:
            f = open(filePath,'r')
            findLine = ''.join((line for line in f if "am_anr  : " in line))
            find = re.findall("(?<=am_anr  : \[)\d+,.*(?=,\d+)", findLine)
            current = dict((i, [j.split(',')[1] for j in find].count(i)) for i in [j.split(',')[1] for j in find])
            self.anr = dict((n, self.anr.get(n, 0) + current.get(n, 0)) for n in set(self.anr) | set(current))
        print '---> Done'

class KernelLog(object):
    def __init__(self, filePaths):
        self.filePaths = filePaths
        self.sigkill = {}
        self.oom = 0
        self._parse()

    def _parse(self):
        print '---> Start parsing kernel logs...'
        for filePath in self.filePaths:
            f = open(filePath,'r')
            findLine = ''.join((line for line in f if "send sigkill to" in line or "invoked oom-killer" in line))
            find = re.findall("(?<=oom_adj )\d+(?=,)", findLine)
            current = dict((i, find.count(i)) for i in find)
            self.sigkill = dict( (n, self.sigkill.get(n, 0) + current.get(n, 0)) for n in set(self.sigkill) | set(current) )
            find = re.findall("invoked oom-killer", findLine)
            self.oom = self.oom + len(find)
        print '---> Done'

class Bugreport(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.project = None
        self.romVersion = None
        self.serial = None
        self._parse()

    def _parse(self):
        print '---> Start parsing bugreport log...'
        try:
            f = open(self.filePath,'r')
            findLine = ''.join((line for line in f if "ro.build.project" in line or "ro.build.description" in line or "ro.serialno" in line))

            find = re.search("(?<=\[ro\.build\.project\]: \[).*(?=\])", findLine)
            if find:
                self.project = find.group().split(':')[0]

            find = re.search("(?<=\[ro\.build\.description\]: \[).*(?=\])", findLine)
            if find:
                result = re.search("#\d+(?=\) test-keys)", find.group())
                if result:
                    self.romVersion = 'CL' + result.group()
                elif "release-keys" in find.group():
                    self.romVersion = find.group().split()[0]

            find = re.search("(?<=\[ro\.serialno\]: \[).*(?=\])", findLine)
            if find:
                self.serial = find.group()
        except:
            print '---> WARNING! THERE IS NO BUGREPORT! SHOULD ENTER <PROJECT><ROM VERSION> MANUALLY!'
            if self.project == None:
                self.project = raw_input('Please enter PROJECT NAME: ')
            if self.romVersion == None:
                self.romVersion = raw_input('Please enter ROM VERSION: ')
            if self.serial == None:
                self.serial = raw_input('Please enter SERIAL NO (optional, enter for empty): ')
        print '---> Done'

class Kmemleak(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.leak = {}
        self._parse()

    def _parse(self):
        print '---> Start parsing kmemleak memlog...'
        try:
            fileObject = open(self.filePath, 'r').read()
        except:
            print '---> WARNING! THERE IS NO KMEMLEAK FILE!'
            return
        chunks = fileObject.split('unreferenced object')

        for chunk in chunks:
            lines = chunk.split('\n')
            backtrace = ''
            command = ''
            size = ''
            function = ''
            for line in lines:
                findCommand = re.search("(?<=comm \").*(?=\")", line)
                if findCommand:
                    command = findCommand.group()
                    continue
                findTrace = re.search("(?<=\[<[0-9a-f]{8}>\] ).*(?=\+)", line)
                if findTrace:
                    backtrace = backtrace + findTrace.group() + '\n'
                    continue
                findSize = re.search("(?<=\(size )\d+(?=\))", line)
                if findSize:
                    size = findSize.group()
                    continue
            if backtrace != '' and command != '' and size != '':
                if not self.leak.has_key((command, size, backtrace[:-1])):
                    self.leak[(command, size, backtrace[:-1])] = 0
                self.leak[(command, size, backtrace[:-1])] = self.leak[(command, size, backtrace[:-1])] + 1
        print '---> Done'

class PDFGen(object):
    Date = datetime.datetime.now().strftime("%Y-%m-%d")
    FileLeft = None
    FileRight = None
    Color = [colors.red, colors.blue, colors.green, colors.pink, colors.gray, colors.cyan, colors.orange, colors.purple, colors.yellow, colors.black]

    def drawLineChart(self, (names, start, end, data, title), reserved=None):
        w = PAGE_WIDTH - 2 * inch
        h = w * 0.6
        drawing = Drawing(w, h)

        lp = LinePlot()
        lp.x = 0
        lp.y = 0
        lp.height = h - 30
        lp.width = w
        lp.data = data
        lp.joinedLines = 1
        lp.strokeColor = colors.black

        lp.xValueAxis = XValueAxis()
        lp.xValueAxis.valueMin = start
        lp.xValueAxis.valueMax = end
        lp.xValueAxis.valueSteps = [(start + i * (end - start) / 5) for i in range(6)]
        lp.xValueAxis.labelTextFormat = lambda seconds: time.strftime("%m/%d %H:%M", time.localtime(seconds))
        lp.xValueAxis.labels.angle = 35
        lp.xValueAxis.labels.fontName = 'Helvetica'
        lp.xValueAxis.labels.fontSize = 7
        lp.xValueAxis.labels.dy = -10
        lp.xValueAxis.labels.boxAnchor = 'e'
        lp.yValueAxis.labelTextFormat = lambda value: '%d MB' % (int(value) / 1000)
        lp.yValueAxis.labels.fontName = 'Helvetica'
        lp.yValueAxis.labels.fontSize = 7
        lp.yValueAxis.visibleGrid = True
        lp.yValueAxis.drawGridLast = True
        lp.yValueAxis.valueMin = 0
        if reserved:
            if reserved[0]: lp.yValueAxis.valueMax = reserved[0]
            if reserved[1]: lp.yValueAxis.valueStep = reserved[1]

        for i in range(len(names)):
            lp.lines[i].strokeColor = self.Color[i]

        legend = Legend()
        legend.x = 0
        legend.y = h - 30
        legend.boxAnchor = 'sw'
        legend.colorNamePairs = [(self.Color[i], names[i]) for i in range(len(names))]
        legend.fontName = 'Helvetica'
        legend.fontSize = 8
        legend.dxTextSpace = 5
        legend.dy = 5
        legend.dx = 5
        legend.deltay = 5
        legend.alignment ='right'

        drawing.add(lp)
        drawing.add(legend)

        if title != None:
            label = Label()
            label.x = w
            label.y = h - 25
            label.boxAnchor = 'se'
            label.fontName = 'Helvetica'
            label.fontSize = 10
            label.setText(title)
            drawing.add(label)
        return drawing

    def drawTable(self, data):
        t = Table(data, None, None, None, 1, 1, 1)
        extraStyle = []
        for i in range(len(data[1:])):
            if data[1:][i][0] == 'Free' or data[1:][i][0] == 'Used':
                extraStyle.append(('BACKGROUND', (0, i + 1), (-1, i + 1), colors.orange))
            if data[1:][i][0] == 'SwapUsage' or data[1:][i][0] == 'LMK File':
                extraStyle.append(('BACKGROUND', (0, i + 1), (-1, i + 1), colors.lightgreen))
        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.deepskyblue),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                               ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
                               ('TOPPADDING', (0, 0), (-1, -1), 4),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                               ] + extraStyle))
        t.hAlign = 'LEFT'
        return t

    def drawCoverPage(self, canvas, doc):
        title = 'Memory Analysis'
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 220, title)
        canvas.setFont('Helvetica', 12)
        canvas.drawCentredString(PAGE_WIDTH / 2.0 + 100, PAGE_HEIGHT - 250, self.Date)
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawContentPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def generate(self, meminfo, procrank, events, kernel, kmemleak, bugreport, output):
        save = None
        if output == None:
            save = 'SST Memory Analysis %s' % self.Date
        else:
            if output.endswith(('.pdf', '.PDF')):
                save = output[:-4]
            else:
                save = output
        doc = SimpleDocTemplate(save + '.pdf')
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())
        print '---> Start summarizing memory analysis...'
        story.append(Paragraph('SST Memory Analysis', Styles['Heading1']))
        story.append(Paragraph('[%s]_[%s]' % (bugreport.project, bugreport.romVersion) + (('_[%s]' % bugreport.serial) if len(bugreport.serial) > 0 else ''), Styles['Normal']))
        story.append(Paragraph('\n', Styles['Normal']))
        start = time.mktime(time.strptime(meminfo.meminfo['MemTotal'][0][-1], "%Y-%m-%d %H:%M:%S"))
        end = time.mktime(time.strptime(meminfo.meminfo['MemTotal'][-1][-1], "%Y-%m-%d %H:%M:%S"))
        duration = end - start
        day = int(duration) / (3600 * 24)
        hour = int(duration - day * 3600 * 24) / 3600
        minute = int(duration - day * 3600 * 24 - hour * 3600) / 60
        story.append(Paragraph('Start Time: %s' % time.strftime("%Y/%m/%d %H:%M", time.localtime(start)), Styles['Normal']))
        story.append(Paragraph('End Time: %s' % time.strftime("%Y/%m/%d %H:%M", time.localtime(end)), Styles['Normal']))
        story.append(Paragraph('Duration: %d Day %02d HR %02d MIN' % (day, hour, minute) , Styles['Normal']))
        story.append(Paragraph('\n', Styles['Normal']))
        story.append(Paragraph('<u>Summary</u>', Styles['Heading2']))
        story.append(Paragraph('System Memory Leakage', Styles['Normal'], u'\u25a0'))
        leakage = []
        for item in meminfo.Summary:
            if meminfo.hasLeakage(item):
                leakage.append(item)
        if len(leakage): story.append(Paragraph('Yes, the following meminfo items may have leakage:<br/><b>%s</b><br/> <br/>' % ' '.join(leakage), Styles['Normal']))
        else: story.append(Paragraph('N<br/> <br/>', Styles['Normal']))
        story.append(Paragraph('Kernel Memory Leakage', Styles['Normal'], u'\u25a0'))
        story.append(Paragraph('None<br/> <br/>', Styles['Normal']))
        story.append(Paragraph('ANR, LMK send sigkill and oom kill Count', Styles['Normal'], u'\u25a0'))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable([['am_anr', 'send sigkill (LMK)', 'oom killer'], [sum(events.anr.values()) if len(events.filePaths) else 'none', sum(kernel.sigkill.values()) if len(kernel.filePaths) else 'none', kernel.oom if len(kernel.filePaths) else 'none']]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('Memory Usage', Styles['Normal'], u'\u25a0'))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(meminfo.tableData(meminfo.Summary)))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('* Free = MemFree + Cached + SwapCached - Mlocked - Shmem', Styles['Tips']))
        story.append(Paragraph('* Used = AnonPages + Slab + VmallocAlloc + Mlocked + Shmem + KernelStack + PageTables + KGSL_ALLOC + ION_ALLOC', Styles['Tips']))
        story.append(Paragraph('* SwapUsage = SwapTotal - SwapFree', Styles['Tips']))
        story.append(Paragraph('* LMK File = Cached + Buffers + SwapCached - Mlocked - Shmem<br/> <br/>', Styles['Tips']))
        story.append(Paragraph('<u>ANR Count Statistic</u>', Styles['Heading2']))
        story.append(self.drawTable([['Process', 'am_anr', '%']] + ([[proc, events.anr[proc], '%d' % (100.0 * events.anr[proc] / sum(events.anr.values()))] for proc in sorted(events.anr.keys(), key=lambda x: events.anr[x], reverse=True)] if len(events.anr) else [['', '', '']])))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('<u>Send Sigkill Count Statistic</>', Styles['Heading2']))
        story.append(self.drawTable([['send sigkill level', 'count'], ['total', sum(kernel.sigkill.values())], ['oom_adj <= 7', sum([kernel.sigkill[key] for key in filter(lambda x: x <= 7, kernel.sigkill.keys())])]]))
        print '---> Done'
        story.append(Spacer(1, 0.2 * inch))
        story.append(PageBreak())

        print '---> Start drawing meminfo tables and charts...'
        story.append(Paragraph('<u>Meminfo Analysis</u>', Styles['Heading2']))
        story.append(self.drawTable(meminfo.tableData(meminfo.Items)))
        story.append(Spacer(1, 0.2 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['KGSL_ALLOC', 'Used', 'MemFree'])))
        story.append(Spacer(1, 0.2 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['Free', 'Cached', 'AnonPages', 'Used']), (meminfo.ram, 100000 if meminfo.ram > 512000 else 50000)))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('* Free = MemFree + Cached + SwapCached - Mlocked - Shmem', Styles['Tips']))
        story.append(Paragraph('* Used = AnonPages + Slab + VmallocAlloc + Mlocked + Shmem + KernelStack + PageTables + KGSL_ALLOC + ION_ALLOC', Styles['Tips']))
        story.append(Spacer(1, 0.5 * inch))
        items = meminfo.inRange(['Buffers', 'Mlocked', 'Shmem', 'Slab', 'KernelStack', 'PageTables', 'VmallocAlloc', 'ION_ALLOC', 'ION_Alloc'], 80000 if meminfo.ram > 1000000 else 40000)
        if (len(items) > 0):
            story.append(self.drawLineChart(meminfo.drawingData(items), (80000 if meminfo.ram > 1000000 else 40000, 10000 if meminfo.ram > 1000000 else 5000)))
            story.append(Spacer(1, 0.5 * inch))
        items = meminfo.overRange(['Buffers', 'Mlocked', 'Shmem', 'Slab', 'KernelStack', 'PageTables', 'VmallocAlloc', 'ION_ALLOC', 'ION_Alloc'], 80000 if meminfo.ram > 1000000 else 40000)
        if (len(items) > 0):
            story.append(self.drawLineChart(meminfo.drawingData(items)))
            story.append(Spacer(1, 0.5 * inch))
        story.append(PageBreak())
        print '---> Done'
        print '---> Start drawing procrank tables and charts...'
        if procrank.ram:
            story.append(Paragraph('<u>Procrank Analysis</u>', Styles['Heading2']))
            story.append(Paragraph('TOP20 procrank', Styles['Normal'], u'\u25a0'))
            story.append(Spacer(1, 0.1 * inch))
            story.append(self.drawTable(procrank.tableData(procrank.topProcs())))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('Specific procrank', Styles['Normal'], u'\u25a0'))
            story.append(Spacer(1, 0.1 * inch))
            story.append(self.drawTable(procrank.tableData(procrank.hotProcs())))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('PSS Peak above %s MB' % procrank.RAMS[procrank.ram][0][1], Styles['Normal'], u'\u25a0'))
            story.append(Spacer(1, 0.1 * inch))
            for procs in [procrank.peakHighProcs()[i:i+3] for i in range(0,len(procrank.peakHighProcs()), 3)]:
                story.append(self.drawLineChart(procrank.drawingData(procs), (1000 * procrank.RAMS[procrank.ram][0][2], 1000 * procrank.RAMS[procrank.ram][1][2])))
                story.append(Spacer(1, 0.6 * inch))
            story.append(Paragraph('PSS Peak between %s MB and %s MB' % (procrank.RAMS[procrank.ram][0][0], procrank.RAMS[procrank.ram][0][1]), Styles['Normal'], u'\u25a0'))
            story.append(Spacer(1, 0.1 * inch))
            for procs in [procrank.peakMediumProcs()[i:i+3] for i in range(0, len(procrank.peakMediumProcs()), 3)]:
                story.append(self.drawLineChart(procrank.drawingData(procs), (1000 * procrank.RAMS[procrank.ram][0][1], 1000 * procrank.RAMS[procrank.ram][1][1])))
                story.append(Spacer(1, 0.6 * inch))
            story.append(Paragraph('PSS Peak below %s MB' % procrank.RAMS[procrank.ram][0][0], Styles['Normal'], u'\u25a0'))
            story.append(Spacer(1, 0.1 * inch))
            for procs in [procrank.peakLowProcs()[i:i+3] for i in range(0, len(procrank.peakLowProcs()), 3)]:
                story.append(self.drawLineChart(procrank.drawingData(procs), (1000 * procrank.RAMS[procrank.ram][0][0], 1000 * procrank.RAMS[procrank.ram][1][0])))
                story.append(Spacer(1, 0.6 * inch))
            story.append(PageBreak())
        print '---> Done'
        print '---> Start drawing kmemleak tables...'
        story.append(Paragraph('<u>Kmem Leakage Analysis</u>', Styles['Heading2']))
        story.append(self.drawTable([['Process', 'Function', 'Hit count', 'Size', 'Leakage', 'Pattern']] + [[key[0], ''.join([PATTERN[function] if function else '' for function in PATTERN.keys() if key[2].find(function) != -1]), kmemleak.leak[key], key[1], '', key[2]] for key in kmemleak.leak.keys()]))
        print '---> Done'
        print '---> Start generating report in PDF ...'
        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)
        print '---> Done'
        print '---> Please check generated PDF at <' + save + '.pdf>'

def _Main(argv):
    opt_parser = optparse.OptionParser("%prog [options] directory")
    opt_parser.add_option('-o', '--output', dest='output',
        help='Use <FILE> to store the generated report', metavar='FILE')
    (opts, args) = opt_parser.parse_args(argv)

    if len(args) != 1:
        opt_parser.print_help()
        sys.exit(1)

    elogs = []
    klogs = []
    plog = ''
    mlog = ''
    llog = ''
    blog = ''
    for (dirpath, dirnames, filenames) in os.walk(args[0]):
        for filename in filenames:
            if filename.startswith('events_'):
                elogs.append(dirpath + '/' + filename)
            if filename.startswith('kernel_'):
                klogs.append(dirpath + '/' + filename)
            if re.match('memlog_\d{8}_\d+\.txt', filename):
                mlog = dirpath + '/' + filename
            if re.match('memlog_\d{8}_\d+_procrank\.txt', filename):
                plog = dirpath + '/' + filename
            if re.match('memlog_\d{8}_\d+_kmemleak\.txt', filename):
                llog = dirpath + '/' + filename
            if filename.startswith('bugreport'):
                blog = dirpath + '/' + filename

    bugreport = Bugreport(blog)
    kmemleak = Kmemleak(llog)
    events = EventsLog(elogs)
    kernel = KernelLog(klogs)
    meminfo = Meminfo(mlog)
    procrank = Procrank(plog)
    pdf = PDFGen()
    pdf.generate(meminfo, procrank, events, kernel, kmemleak, bugreport, opts.output)

if __name__ == '__main__':
    _Main(sys.argv[1:])
