import re
import time
import datetime

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
        fileObject = open(self.filePath, 'r').read()
        print '---> Start parsing meminfo memlog ...'
        chunks = fileObject.split('------ MEMORY INFO')
        dates = []
        self.meminfo['Free'] = []
        self.meminfo['Used'] = []
        self.meminfo['SwapUsage'] = []
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
            self.meminfo['SwapUsage'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) * self.SwapUsage[value] for value in filter(lambda x: self.meminfo.has_key(x), self.SwapUsage.keys())]), date])
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

class Procrank(object):
    RAMS = {512: ((20, 50, 200), (2, 5, 20)), 768: ((20, 50, 200), (2, 5, 20)), 1024: ((50, 100, 500), (5, 10, 50)), 2048: ((50, 100, 500), (5, 10, 50))}
    def __init__(self, filePath):
        self.procrank = {}
        self.dates = []
        self.ram = 0
        self.filePath = filePath
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        print '---> Start parsing procrank memlog ...'
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
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (-1, 0), 2, colors.black),
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

    def generate(self, meminfo, procrank):
        doc = SimpleDocTemplate('memory analysis report.pdf')
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())
        print '---> Start generate memory analysis summary...'
        story.append(Paragraph('SST Memory Analysis', Styles['Heading1']))
        story.append(Paragraph('[Project]_[ROM version]{_[SerialNo]}', Styles['Normal']))
        story.append(Paragraph('\n', Styles['Normal']))
        story.append(Paragraph('<u>Summary</u>', Styles['Heading2']))
        story.append(Paragraph('System Memory Leakage', Styles['Normal'], u'\u25a0'))
        story.append(Paragraph('N<br/> <br/>', Styles['Normal']))
        story.append(Paragraph('Kernel Memory Leakage', Styles['Normal'], u'\u25a0'))
        story.append(Paragraph('None<br/> <br/>', Styles['Normal']))
        story.append(Paragraph('ANR and LMK Count', Styles['Normal'], u'\u25a0'))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable([['am_anr', 'send sigkill (LMK)'], [12, 278]]))
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
        story.append(self.drawTable([['Process', 'am_anr', '%'], ['com.facebook.katana', '34', '68'], ['com.android.nfc', '12', '24'], ['com.android.vending', '4', '8']]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('<u>Send Sigkill Count Statistic</>', Styles['Heading2']))
        story.append(self.drawTable([['send sigkill level', 'count'], ['total', '278'], ['oom_adj <= 7', '0']]))
        print '---> Done'
        story.append(Spacer(1, 0.2 * inch))
        story.append(PageBreak())

        print '---> Start drawing table of average and peak meminfo items ...'
        story.append(Paragraph('<u>Meminfo Analysis</u>', Styles['Heading2']))
        story.append(self.drawTable(meminfo.tableData(meminfo.Items)))
        story.append(Spacer(1, 0.2 * inch))
        print '---> Done'
        print '---> Start drawing chart of meminfo items...'
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
        print '---> Done'
        print '---> Start drawing table of average and peak procrank items ...'
        story.append(PageBreak())
        story.append(Paragraph('<u>Procrank Analysis</u>', Styles['Heading2']))
        story.append(Paragraph('TOP20 procrank', Styles['Normal'], u'\u25a0'))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.topProcs())))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('Specific procrank', Styles['Normal'], u'\u25a0'))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.hotProcs())))
        story.append(Spacer(1, 0.2 * inch))
        print '---> Done'
        print '---> Start drawing chart of processes in procrank ...'
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
        print '---> Done'
        print '---> Start generate report in PDF ...'
        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)
        print '---> Done'

def _Main():
    meminfo = Meminfo('memlog.txt')
    procrank = Procrank('memlog_procrank.txt')

    pdf = PDFGen()
    pdf.generate(meminfo, procrank)

if __name__ == '__main__':
    _Main()
