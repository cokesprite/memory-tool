#!/usr/bin/python

import sys
import optparse
import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.tables import TableStyle
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize

class BRInfo(object):

    def __init__(self, filePath):
        self.filePath = filePath
        self.meminfo = []
        self.procrank = {}
        self.proc = []
        self.parseBugReport()

    def parseBugReport(self):
        fileObject = open(self.filePath, 'r').read()

        meminfoStart = fileObject.find("------ MEMORY INFO")
        for line in fileObject[meminfoStart:].split('\n')[1:45]:
            formated = line.split()
            self.meminfo.append((formated[0][:-1], formated[1]))

        procrankStart = fileObject.find("------ PROCRANK")
        procrankEnd = fileObject.find("------   ------  ------")
        for line in fileObject[procrankStart:procrankEnd].split('\n')[2:-1]:
            formated = line.split()
            self.proc.append(formated[-1])
            self.procrank[formated[-1]]=formated[0:-1]

class BRCompare(object):

    def execute(self, left, right):
        meminfo = []
        procrank = []
        meminfo.append(['Item', 'A: %s' % left.filePath, 'B: %s' % right.filePath, 'Diff: A-B'])
        procrank.append(['cmdline', 'A: %s\nB: %s' % (left.filePath, right.filePath), 'PID', 'Vss', 'Rss', 'Pss', 'Uss'])
        for i, j in zip(left.meminfo, right.meminfo):
            meminfo.append([i[0], i[1], j[1], '%d' % (int(i[1]) - int(j[1]))])

        for i in left.proc:
            procrank.append([i, 'A'] + left.procrank[i])
            if right.procrank.has_key(i):
                rightValues = right.procrank.pop(i)
                procrank.append([i, 'B'] + rightValues)
                procrank.append(['', 'Diff: A-B', '-',
                                '%dK' % (int(left.procrank[i][1][:-1]) - int(rightValues[1][:-1])),
                                '%dK' % (int(left.procrank[i][2][:-1]) - int(rightValues[2][:-1])),
                                '%dK' % (int(left.procrank[i][3][:-1]) - int(rightValues[3][:-1])),
                                '%dK' % (int(left.procrank[i][4][:-1]) - int(rightValues[4][:-1])),
                                ])
            else:
                procrank.append([i, 'B', '-', '-', '-', '-', '-'])
                procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])
        for i in right.proc:
            if right.procrank.has_key(i):
                procrank.append([i, 'A', '-', '-', '-', '-', '-'])
                procrank.append([i, 'B'] + right.procrank[i])
                procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])

        pdf = PDFGen()
        pdf.generate(meminfo, procrank)

class PDFGen(object):
    Title = 'Bugreport Comparision - Meminfo and Procrank'
    Date = datetime.datetime.now().strftime("%Y-%m-%d")

    (PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
    Styles = getSampleStyleSheet()

    def drawCoverPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 220, self.Title)
        canvas.setFont('Helvetica', 12)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0 + 100, self.PAGE_HEIGHT - 250, self.Date)
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawContentPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawMeminfo(self, data):
        t = Table(data, None, None, None, 1, 1)
        t.setStyle(TableStyle([('FONT', (0,0), (-1,-1), 'Helvetica'),
                               ('BACKGROUND', (0,0), (-1,0), colors.green),
                               ('FONTSIZE', (0,0), (-1,-1), 8),
                               ('GRID', (0,0), (-1,-1), 1, colors.black),
                               ('BOX', (0,0), (-1,-1), 2, colors.black),
                               ('BOX', (0,0), (-1,0), 2, colors.black),
                               ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                               ('TOPPADDING', (0,0), (-1,-1), 1),
                               ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                               ]))
        return t

    def drawProcrank(self, data):
        t = Table(data, None, None, None, 1, 1)
        styles = []
        for i in range(len(data)):
            if i !=0 and i % 3 == 1:
                styles.append(('SPAN', (0, i), (0, i + 2)))

        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (-1, 0), 2, colors.black),
                               ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ] + styles
                               ))
        return t

    def generate(self, meminfo=None, procrank=None, output=None):
        filePath = ''
        if output != None:
            filePath = output
        else:
            filePath = 'Bugreport Comparision %s.pdf' % self.Date
        doc = SimpleDocTemplate(filePath)
        style = self.Styles["Normal"]
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())

        if meminfo:
            meminfoTitle = Paragraph('Meminfo Comparision', style)
            story.append(meminfoTitle)
            meminfoTable = self.drawMeminfo(meminfo)
            story.append(meminfoTable)
            story.append(PageBreak())

        if procrank:
            procrankTitle = Paragraph('Procrank Comparision', style)
            story.append(procrankTitle)
            procrankTable = self.drawProcrank(procrank)
            story.append(procrankTable)

        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)

def _Main(argv):
    opt_parser = optparse.OptionParser("%prog [options] file1 file2")
    opt_parser.add_option('-m', '--meminfo', action="store_true", dest="meminfo",
        help="Compare meminfo in two bugreport logs")
    opt_parser.add_option('-p', '--procrank', action="store_true", dest="procrank",
        help="Compare procrank in two bugreport logs")
    (opts, args) = opt_parser.parse_args(argv)

    if len(args) != 2:
        opt_parser.print_help()
        sys.exit(1)
    else:
        compare = BRCompare()
        compare.execute(BRInfo(args[0]), BRInfo(args[1]))

if __name__ == '__main__':
    _Main(sys.argv[1:])
