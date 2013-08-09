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

class Meminfo(object):
    def fromData(self, data):
        meminfoItem = []
        meminfo = {}
        for line in data:
            formated = line.split()
            meminfoItem.append(formated[0][:-1])
            meminfo[formated[0][:-1]]=formated[1]
        return (meminfoItem, meminfo)

class Procrank(object):
    def fromData(self, data):
        proc = []
        procrank = {}
        for line in data:
            formated = line.split()
            proc.append(formated[-1])
            procrank[formated[-1]]=[formated[0], formated[1][:-1], formated[2][:-1], formated[3][:-1], formated[4][:-1]]
        return (proc, procrank)

class InputInfo(object):

    def __init__(self, filePath):
        self.filePath = filePath
        self.meminfo = {}
        self.procrank = {}
        self.meminfoItem = []
        self.proc = []

    def parseMeminfo(self):
        fileObject = open(self.filePath, 'r').read()
        meminfo = Meminfo()
        (self.meminfoItem, self.meminfo) = meminfo.fromData(fileObject.split('\n')[:-1])

    def parseProcrank(self):
        fileObject = open(self.filePath, 'r').read()
        procrank = Procrank()
        (self.proc, self.procrank) = procrank.fromData(fileObject.split('\n')[1:-5])

    def parseBugreport(self):
        fileObject = open(self.filePath, 'r').read()

        meminfoStart = fileObject.find("------ MEMORY INFO")
        meminfoEnd = fileObject.find("------ CPU INFO")
        meminfo = Meminfo()
        (self.meminfoItem, self.meminfo) = meminfo.fromData(fileObject[meminfoStart:meminfoEnd].split('\n')[1:-2])

        procrankStart = fileObject.find("------ PROCRANK")
        procrankEnd = fileObject.find("------ VIRTUAL MEMORY STATS")
        if fileObject[procrankStart:procrankEnd].find("Permission denied") == -1:
            procrank = Procrank()
            (self.proc, self.procrank) = procrank.fromData(fileObject[procrankStart:procrankEnd].split('\n')[2:-7])

class Compare(object):

    def execute(self, left, right, output=None):
        pdf = PDFGen()

        meminfo = []
        if len(left.meminfoItem) > 0 and len(right.meminfoItem) > 0:
            print "meminfo"
            meminfo.append(['Item', 'A: %s' % left.filePath, 'B: %s' % right.filePath, 'Diff: A-B'])
            for i in left.meminfoItem:
                if right.meminfo.has_key(i):
                    rightValues = right.meminfo.pop(i)
                    meminfo.append(['%s (KB)' % i, '%d' % (int(left.meminfo[i]) / 1000), '%d' % (int(rightValues) / 1000), '%d' % ((int(left.meminfo[i]) - int(rightValues)) / 1000)])
                else:
                    meminfo.append(['%s (KB)' % i, '%d' % (int(left.meminfo[i]) / 1000), '-', '-'])
            for i in right.meminfoItem:
                if right.meminfo.has_key(i):
                    meminfo.append(['%s (KB)' % i, '-', '%d' % (int(right.meminfo[i]) / 1000), '-'])

        procrank = []
        if len(left.proc) > 0 and len(right.proc) > 0:
            print "procrank"
            procrank.append(['cmdline', 'A: %s\nB: %s' % (left.filePath, right.filePath), 'PID', 'Vss (KB)', 'Rss (KB)', 'Pss (KB)', 'Uss (KB)'])
            for i in left.proc:
                procrank.append([i, 'A'] + left.procrank[i])
                if right.procrank.has_key(i):
                    rightValues = right.procrank.pop(i)
                    procrank.append([i, 'B'] + rightValues)
                    procrank.append(['', 'Diff: A-B', '-',
                                    '%d' % (int(left.procrank[i][1][:-1]) - int(rightValues[1][:-1])),
                                    '%d' % (int(left.procrank[i][2][:-1]) - int(rightValues[2][:-1])),
                                    '%d' % (int(left.procrank[i][3][:-1]) - int(rightValues[3][:-1])),
                                    '%d' % (int(left.procrank[i][4][:-1]) - int(rightValues[4][:-1])),
                                    ])
                else:
                    procrank.append([i, 'B', '-', '-', '-', '-', '-'])
                    procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])
            for i in right.proc:
                if right.procrank.has_key(i):
                    procrank.append([i, 'A', '-', '-', '-', '-', '-'])
                    procrank.append([i, 'B'] + right.procrank[i])
                    procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])

        pdf.generate(meminfo, procrank, output)

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

    def generate(self, meminfo, procrank, output=None):
        filePath = ''
        if output != None:
            filePath = output
        else:
            filePath = 'Bugreport Comparision %s.pdf' % self.Date
        doc = SimpleDocTemplate(filePath)
        style = self.Styles["Normal"]
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())

        if len(meminfo) > 0:
            meminfoTitle = Paragraph('Meminfo Comparision', style)
            story.append(meminfoTitle)
            meminfoTable = self.drawMeminfo(meminfo)
            story.append(meminfoTable)
            story.append(PageBreak())

        if len(procrank) > 0:
            procrankTitle = Paragraph('Procrank Comparision', style)
            story.append(procrankTitle)
            procrankTable = self.drawProcrank(procrank)
            story.append(procrankTable)
        #else:
        #    procrankTitle = Paragraph('Fail to generate procrank comparisn! Procrank info is missing!', style)
        #    story.append(procrankTitle)

        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)

def _Main(argv):
    opt_parser = optparse.OptionParser("%prog [options] file1 file2")
    opt_parser.add_option('-m', '--meminfo', action='store_true', dest='meminfo', default=False,
        help='Compare two meminfo files [invalid now]')
    opt_parser.add_option('-p', '--procrank', action="store_true", dest="procrank", default=False,
        help='Compare two procrank files [invalid now]')
    opt_parser.add_option('-b', '--bugreport', action="store_true", dest="bugreport", default=False,
        help='Compare two bugreport files')
    opt_parser.add_option('-o', '--output', dest='output',
        help='Use <FILE> to store the generated report', metavar='FILE')
    (opts, args) = opt_parser.parse_args(argv)
    if (opts.meminfo + opts.procrank + opts.bugreport) > 1:
        opt_parser.error("options -m, -p and -b are mutually exclusive")
    if (opts.meminfo + opts.procrank + opts.bugreport) == 0:
        opts.bugreport = True

    if len(args) != 2:
        opt_parser.print_help()
        sys.exit(1)
    else:
        compare = Compare()
        left = InputInfo(args[0])
        right = InputInfo(args[1])
        if opts.bugreport:
            left.parseBugreport()
            right.parseBugreport()
        if opts.meminfo:
            left.parseMeminfo()
            right.parseMeminfo()
        if opts.procrank:
            left.parseProcrank()
            right.parseProcrank()
        compare.execute(left, right, opts.output)

if __name__ == '__main__':
    _Main(sys.argv[1:])
