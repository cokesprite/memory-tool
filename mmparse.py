import re
import time
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import GridLinePlot, LinePlot, sample2
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.charts.axes import NormalDateXValueAxis, XValueAxis
from reportlab.graphics.widgets.markers import makeMarker

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
            date = re.search('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d', lines[0])
            date = date.group()
            for line in lines[2:-5]:
                formated = line.split()
                if self.procrank.has_key(formated[-1]):
                    proc = self.procrank[formated[-1]]
                    proc.append(formated[1:-1] + [date])
                    self.procrank[formated[-1]] = proc
                else:
                    self.procrank[formated[-1]] = [formated[1:-1] + [date]]

    def topProcs(self):
        return sorted(self.procrank.keys(), key=lambda proc: reduce(lambda x, y: x + y, [int(value[2][:-1]) for value in self.procrank[proc]]) / len(self.procrank[proc]), reverse=True)[:20]

    def hotProcs(self):
        return ['com.htc.launcher', 'surfaceflinger', 'system_server', 'com.android.browser', 'android.process.acore',
                'com.android.phone', 'com.android.systemui', 'com.htc.idlescreen.shortcut', 'com.android.chrome',
                'com.android.launcher', 'com.android.htcdialer', 'com.htc.android.htcime']

    def drawing(self, proc):
        dates = map(lambda tstring: time.mktime(time.strptime(tstring, "%Y-%m-%d %H:%M:%S")), [value[4] for value in self.procrank[proc]])
        data = [
            zip(dates, [int(value[1][:-1]) for value in self.procrank[proc]]),
            zip(dates, [int(value[2][:-1]) for value in self.procrank[proc]]),
            ]

        drawing = Drawing(500, 300)

        lp = GridLinePlot()
        lp.x = 50
        lp.y = 50
        lp.height = 225
        lp.width = 425
        lp.data = data
        lp.joinedLines = 1
        lp.strokeColor = colors.black

        start = dates[0]
        end = dates[-1]
        delta = (end - start) / 3
        lp.xValueAxis = XValueAxis()
        lp.xValueAxis.valueMin = start
        lp.xValueAxis.valueMax = end
        lp.xValueAxis.valueSteps = [start, start + delta, start + 2 * delta, end]
        lp.xValueAxis.labelTextFormat = lambda seconds: time.strftime("%d/%m %H:%M", time.localtime(seconds))
        lp.xValueAxis.labels.angle = 35
        lp.xValueAxis.labels.dy = -10
        lp.xValueAxis.labels.boxAnchor = 'e'
        lp.yValueAxis.labelTextFormat = lambda value: '%d MB' % (int(value) / 1000)

        drawing.add(lp)

        return drawing


class PDFGen(object):
    Date = datetime.datetime.now().strftime("%Y-%m-%d")
    FileLeft = None
    FileRight = None

    (PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
    Styles = getSampleStyleSheet()

    def drawCoverPage(self, canvas, doc):
        title = 'Memory Analysis'
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 220, title)
        canvas.setFont('Helvetica', 12)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 250, 'File A: ')
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 280, 'File B: ')
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0 + 100, self.PAGE_HEIGHT - 310, self.Date)
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawContentPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def generate(self, meminfo, procrank, fileLeft, fileRight, output=None):
        doc = SimpleDocTemplate('haha.pdf')
        style = self.Styles["Normal"]
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())
        story.append(Paragraph('system_server in procrank memlog', style))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        story.append(procrank.drawing('system_server'))
        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)

def _Main():
    print '---> Start parsing ...'
    procrank = Procrank('procrank')
    print '---> Done'

    print '---> Start generate PDF ...'
    pdf = PDFGen()
    pdf.generate(None, procrank, None, None)
    print '---> Done'

if __name__ == '__main__':
    _Main()
