import re
import time
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import GridLinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.charts.axes import XValueAxis
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus.tables import TableStyle

(PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
Styles = {'Normal': ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=10, leading=12),
          'Header1': ParagraphStyle(name='Header', fontName='Helvetica', fontSize=12, leading=12),}

class Meminfo(object):
    def __init__(self, filePath):
        self.meminfo = {}
        self.filePath = filePath
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        print '---> Start parsing meminfo memlog ...'
        chunks = fileObject.split('------ MEMORY INFO')
        for chunk in chunks[1:]:
            lines = chunk.split('\n')
            date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0])
            for i in range(len(lines[1:-2])):
                formated = lines[1:-2][i].split()
                if not self.meminfo.has_key(formated[0][:-1]):
                    self.meminfo[formated[0][:-1]] = []
                self.meminfo[formated[0][:-1]].append([formated[1], date.group()])
        print '---> Done'

    def drawingData(self, items, title=None):
        data = []
        for item in items:
            dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[1] for value in self.meminfo[item]])
            data.append(zip(dates, [int(value[0]) for value in self.meminfo[item]]))
        return (items, dates[0], dates[-1], data, title)

class Procrank(object):
    def __init__(self, filePath):
        self.procrank = {}
        self.filePath = filePath
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        print '---> Start parsing procrank memlog ...'
        chunks = fileObject.split('------ PROCRANK')
        for chunk in chunks[1:]:
            lines = chunk.split('\n')
            date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0])
            date = date.group()
            for line in lines[2:-5]:
                formated = line.split()
                if not self.procrank.has_key(formated[-1]):
                    self.procrank[formated[-1]] = []
                self.procrank[formated[-1]].append(formated[1:-1] + [date])
        print '---> Done'

    def topProcs(self):
        return sorted(self.procrank.keys(), key=lambda proc: reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]), reverse=True)[:20]

    def hotProcs(self):
        return filter(lambda x: self.procrank.has_key(x), ['com.htc.launcher', 'surfaceflinger', 'system_server', 'com.android.browser', 'android.process.acore',
                'com.android.phone', 'com.android.systemui', 'com.htc.idlescreen.shortcut', 'com.android.chrome',
                'com.android.launcher', 'com.android.htcdialer', 'com.htc.android.htcime'])

    def tableData(self, procs):
        return [['Process Name', 'RSS Average (KB)', 'RSS Peak (KB)', 'PSS Average (KB)', 'PSS Peak (KB)']] + [[proc,
                reduce(lambda x, y: x + y, [int(value[1][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]),
                max([int(value[1][:-1]) for value in self.procrank[proc]]),
                reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]),
                max([int(value[2][:-1]) for value in self.procrank[proc]])] for proc in procs]

    def drawingData(self, proc, title=None):
        dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[4] for value in self.procrank[proc]])
        data = [
            zip(dates, [int(value[1][:-1]) for value in self.procrank[proc]]),
            zip(dates, [int(value[2][:-1]) for value in self.procrank[proc]]),
            ]
        return (['RSS', 'PSS'], dates[0], dates[-1], data, title)

class PDFGen(object):
    Date = datetime.datetime.now().strftime("%Y-%m-%d")
    FileLeft = None
    FileRight = None
    Color = [colors.red, colors.blue, colors.green, colors.pink, colors.gray, colors.cyan, colors.orange, colors.purple, colors.yellow, colors.black]

    def drawLineChart(self, (names, start, end, data, title)):
        w = PAGE_WIDTH - 2 * inch
        h = w * 0.6
        drawing = Drawing(w, h)

        lp = GridLinePlot()
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

    def generate(self, meminfo, procrank, fileLeft, fileRight, output=None):
        doc = SimpleDocTemplate('memory analysis report.pdf')
        style = Styles['Normal']
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())
        print '---> Start drawing table of average and peak procrank items ...'
        story.append(Paragraph('Average and Peak RSS/PSS in Procrank (top 20 of memory usage)', style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.topProcs())))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('Average and Peak RSS/PSS in Procrank (pre-defined applications)', style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(self.drawTable(procrank.tableData(procrank.hotProcs())))
        print '---> Done'
        print '---> Start drawing chart of items in meminfo ...'
        story.append(Spacer(1, 0.5 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['MemFree', 'Cached', 'AnonPages'], 'Meminfo First Group')))
        story.append(Spacer(1, 0.5 * inch))
        story.append(self.drawLineChart(meminfo.drawingData(['Buffers', 'Mlocked', 'Shmem', 'Slab', 'KernelStack', 'PageTables', 'VmallocAlloc', 'ION_ALLOC'], 'Meminfo Second Group')))
        story.append(Spacer(1, 0.5 * inch))
        print '---> Done'
        print '---> Start drawing chart of top processes in procrank ...'
        for top in procrank.topProcs():
            story.append(self.drawLineChart(procrank.drawingData(top, 'Process: %s in Procrank' % top)))
            story.append(Spacer(1, 0.5 * inch))
        print '---> Done'
        print '---> Start generate report in PDF ...'
        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)
        print '---> Done'

def _Main():
    meminfo = Meminfo('memlog.txt')
    procrank = Procrank('memlog_procrank.txt')

    pdf = PDFGen()
    pdf.generate(meminfo, procrank, None, None)

if __name__ == '__main__':
    _Main()
