import re
import time
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot, GridLinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.charts.axes import XValueAxis
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus.tables import TableStyle
from reportlab.graphics.widgets.grids import Grid

(PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
Styles = {'Normal': ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=10, leading=12),
          'Tips': ParagraphStyle(name='Header', fontName='Helvetica', fontSize=8, leading=12),
          'Header': ParagraphStyle(name='Header', fontName='Helvetica-Bold', fontSize=12, leading=12),}

class Meminfo(object):
    Free = {'MemFree': 1, 'Cached': 1, 'SwapCached': 1, 'Mlocked': -1, 'Shmem': -1}
    Used = ['AnonPages', 'Slab', 'VmallocAlloc', 'Mlocked', 'Shmem', 'KernelStack', 'PageTables', 'KGSL_ALLOC', 'ION_ALLOC']
    def __init__(self, filePath):
        self.meminfo = {}
        self.filePath = filePath
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        print '---> Start parsing meminfo memlog ...'
        chunks = fileObject.split('------ MEMORY INFO')
        dates = []
        for chunk in chunks[1:]:
            lines = chunk.split('\n')
            date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0]).group()
            dates.append(date)
            for i in range(len(lines[1:-2])):
                formated = lines[1:-2][i].split()
                if len(formated) == 0: break
                if not self.meminfo.has_key(formated[0][:-1]):
                    self.meminfo[formated[0][:-1]] = []
                self.meminfo[formated[0][:-1]].append([formated[1], date])
            if not self.meminfo.has_key('Free'):
                self.meminfo['Free'] = []
            if not self.meminfo.has_key('Used'):
                self.meminfo['Used'] = []
            self.meminfo['Free'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) * self.Free[value] for value in filter(lambda x: self.meminfo.has_key(x), self.Free.keys())]), date])
            self.meminfo['Used'].append([reduce(lambda x, y: x + y, [int(self.meminfo[value][-1][0]) for value in filter(lambda x: self.meminfo.has_key(x), self.Used)]), date])
        print '---> Done'

    def drawingData(self, items, title=None):
        data = []
        for item in items:
            dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[1] for value in self.meminfo[item]])
            data.append(zip(dates, [int(value[0]) for value in self.meminfo[item]]))
        return (items, dates[0], dates[-1], data, title)

class Procrank(object):
    RAMS = {512: (20, 50), 768: (20, 50), 1024: (50, 100), 2048: (50, 100)}
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
            for line in lines[2:-5]:
                formated = line.split()
                if len(formated) == 0: break
                if not self.procrank.has_key(formated[-1]):
                    self.procrank[formated[-1]] = []
                self.procrank[formated[-1]].append(formated[1:-1] + [date])
        print '---> Done'

    def topProcs(self):
        return sorted(self.procrank.keys(), key=lambda proc: reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]), reverse=True)[:20]

    def peakHighProcs(self):
        return sorted(filter(lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]) >= 1000 * self.RAMS[self.ram][1], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)[:10]

    def peakMediumProcs(self):
        return sorted(filter(lambda proc: 1000 * self.RAMS[self.ram][0] <= max([int(value[2][:-1]) for value in self.procrank[proc]]) < 1000 * self.RAMS[self.ram][1], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)[:10]

    def peakLowProcs(self):
        return sorted(filter(lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]) < 1000 * self.RAMS[self.ram][0], self.procrank.keys()), key=lambda proc: max([int(value[2][:-1]) for value in self.procrank[proc]]), reverse=True)[:10]

    def hotProcs(self):
        return filter(lambda x: self.procrank.has_key(x), ['com.htc.launcher', 'surfaceflinger', 'system_server', 'com.android.browser', 'android.process.acore', 'com.android.phone', 'com.android.systemui', 'com.htc.idlescreen.shortcut', 'com.android.chrome', 'com.android.launcher', 'com.android.htcdialer', 'com.htc.android.htcime'])

    def tableData(self, procs):
        return [['Process Name', 'PSS Average (KB)', 'PSS Peak (KB)']] + [[proc,
                reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]),
                max([int(value[2][:-1]) for value in self.procrank[proc]])] for proc in procs]

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

        fakeAxis = []
        if reserved:
            lp.yValueAxis.valueMin = 0
            lp.yValueAxis.valueStep = 100 * 1000
            for i in range(1, 3):
                xAxis = XValueAxis()
                xAxis.joinAxis = lp.yValueAxis
                xAxis.joinAxisMode = 'value'
                xAxis.joinAxisPos = i * 500 * 1000
                xAxis.visibleLabels = False
                xAxis.visibleTicks = False
                xAxis.setPosition(0, 0, lp.width)
                fakeAxis.append(xAxis)

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
        if reserved:
            for axis in fakeAxis:
                drawing.add(axis)

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
        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (-1, 0), 2, colors.black),
                               ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ]))
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
        print '---> Start drawing chart of items in meminfo ...'
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('Meminfo Analysis', Styles['Header']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['Free', 'Cached', 'AnonPages', 'Used']), True))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('* Free = MemFree + Cached + SwapCached - Mlocked - Shmem', Styles['Tips']))
        story.append(Paragraph('* Used = AnonPages + Slab + VmallocAlloc + Mlocked + Shmem + KernelStack + PageTables + KGSL_ALLOC + ION_ALLOC', Styles['Tips']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['Buffers', 'Mlocked', 'Shmem', 'Slab', 'KernelStack', 'PageTables', 'VmallocAlloc', 'ION_ALLOC'])))
        story.append(Spacer(1, 0.5 * inch))
        print '---> Done'
        print '---> Start drawing table of average and peak procrank items ...'
        story.append(PageBreak())
        story.append(Paragraph('Procrank Analysis', Styles['Header']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('Top 20 Procrank', Styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.topProcs())))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('Pre-defined Applications', Styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.hotProcs())))
        print '---> Done'
        print '---> Start drawing chart of top processes in procrank ...'
        story.append(PageBreak())
        story.append(Paragraph('PSS Peak Above %s MB' % procrank.RAMS[procrank.ram][1], Styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawLineChart(procrank.drawingData(procrank.peakHighProcs())))
        story.append(Spacer(1, 0.6 * inch))
        story.append(Paragraph('PSS Peak in (%s MB, %s MB)' % (procrank.RAMS[procrank.ram][0], procrank.RAMS[procrank.ram][1]), Styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawLineChart(procrank.drawingData(procrank.peakMediumProcs())))
        story.append(Spacer(1, 0.6 * inch))
        story.append(Paragraph('PSS Peak Below %s MB' % procrank.RAMS[procrank.ram][0], Styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawLineChart(procrank.drawingData(procrank.peakLowProcs())))
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
