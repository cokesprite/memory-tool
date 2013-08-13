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
from xlwt import Workbook, easyxf

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
            if not formated[-1] in proc:
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
            meminfo.append(['Item', 'A: %s' % left.filePath, 'B: %s' % right.filePath, 'Diff: A-B'])
            for i in left.meminfoItem:
                if right.meminfo.has_key(i):
                    rightValues = right.meminfo.pop(i)
                    meminfo.append([i, '%d KB' % int(left.meminfo[i]), '%d KB' % int(rightValues), '%d KB' % (int(left.meminfo[i]) - int(rightValues))])
                else:
                    meminfo.append([i, '%d KB' % int(left.meminfo[i]), '-', '-'])
            for i in right.meminfoItem:
                if right.meminfo.has_key(i):
                    meminfo.append([i, '-', '%d KB' % int(right.meminfo[i]), '-'])

        procrank = []
        if len(left.proc) > 0 and len(right.proc) > 0:
            procrank.append(['cmdline', 'A: %s\nB: %s' % (left.filePath, right.filePath), 'PID', 'Vss (KB)', 'Rss (KB)', 'Pss (KB)', 'Uss (KB)'])
            for i in left.proc:
                procrank.append(['', 'A'] + left.procrank[i])
                if right.procrank.has_key(i):
                    rightValues = right.procrank.pop(i)
                    procrank.append([i, 'B'] + rightValues)
                    procrank.append(['', 'Diff: A-B', '-',
                                    '%d' % (int(left.procrank[i][1]) - int(rightValues[1])),
                                    '%d' % (int(left.procrank[i][2]) - int(rightValues[2])),
                                    '%d' % (int(left.procrank[i][3]) - int(rightValues[3])),
                                    '%d' % (int(left.procrank[i][4]) - int(rightValues[4])),
                                    ])
                else:
                    procrank.append([i, 'B', '-', '-', '-', '-', '-'])
                    procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])
            for i in right.proc:
                if right.procrank.has_key(i):
                    procrank.append(['', 'A', '-', '-', '-', '-', '-'])
                    procrank.append([i, 'B'] + right.procrank[i])
                    procrank.append(['', 'Diff: A-B', '-', '-', '-', '-', '-'])

        pdf.generate(meminfo, procrank, left.filePath, right.filePath, output)
        a = XLSGen()
        a.generate(meminfo, procrank, None, None, output)

class XLSGen(object):
    VMinBorders = 'top medium, bottom medium,'
    VMaxBorders = 'top thin, bottom medium,'
    VMidBorders = 'top thin, bottom thin,'
    HMinBorders = 'left medium, right thin,'
    HMaxBorders = 'left thin, right medium,'
    HMidBorders = 'left thin, right thin,'

    def generate(self, meminfo, procrank, fileLeft, fileRight, output=None):
        xlsBook = Workbook()
        sheetMeminfo = xlsBook.add_sheet('MEMINFO')
        for rowIndex in range(len(meminfo)):
            for colIndex in range(len(meminfo[0])):
                borders = 'borders: '
                headers = ''
                diffs = ''
                align = ''
                if rowIndex == 0:
                    headers = 'pattern: pattern solid, fore_colour green;'
                    borders = borders + self.VMinBorders
                else:
                    if rowIndex == (len(meminfo) - 1):
                        borders = borders + self.VMaxBorders
                    else:
                        borders = borders + self.VMidBorders
                if colIndex == 0:
                    borders = borders + self.HMinBorders
                else:
                    align = 'alignment: horizontal right;'
                    if colIndex == (len(meminfo[0]) - 1):
                        diffs = 'pattern: pattern solid, fore_colour light_green;'
                        borders = borders + self.HMaxBorders
                    else:
                        borders = borders + self.HMidBorders
                borders = borders + ';'
                xf = easyxf(borders + diffs + headers + align)
                sheetMeminfo.write(rowIndex + 1, colIndex + 1, meminfo[rowIndex][colIndex], xf)

        sheetMeminfo.col(1).width = 5000
        sheetMeminfo.col(2).width = 5000
        sheetMeminfo.col(3).width = 5000
        sheetMeminfo.col(4).width = 5000

        sheetProcrank = xlsBook.add_sheet('PROCRANK')
        for rowIndex in range(len(procrank)):
            for colIndex in range(len(procrank[0])):
                borders = 'borders: '
                headers = ''
                diffs = ''
                align = ''
                if rowIndex == 0:
                    headers = 'pattern: pattern solid, fore_colour green;'
                    borders = borders + self.VMinBorders
                else:
                    if rowIndex == (len(procrank) - 1) and colIndex != 0:
                        borders = borders + self.VMaxBorders
                    else:
                        if colIndex != 0:
                            borders = borders + self.VMidBorders
                if colIndex == 0:
                    if rowIndex % 3 == 1 and rowIndex != (len(procrank) - 1):
                        borders = 'borders: top thin,'
                    else:
                        if rowIndex and rowIndex % 3 == 0 and rowIndex != (len(procrank) - 1):
                            borders = 'borders: bottom thin,'
                        else:
                            if rowIndex and rowIndex != (len(procrank) - 1):
                                borders = 'borders: '
                            else:
                                if rowIndex == 0:
                                    borders = 'borders: top medium, bottom medium,'
                                else:
                                    borders = 'borders: bottom medium,'
                    borders = borders + self.HMinBorders
                else:
                    align = 'alignment: horizontal right;'
                    if rowIndex and rowIndex % 3 ==0:
                        diffs = 'pattern: pattern solid, fore_colour light_green;'
                    if colIndex == (len(procrank[0]) - 1):
                        borders = borders + self.HMaxBorders
                    else:
                        borders = borders + self.HMidBorders
                borders = borders + ';'
                print borders
                xf = easyxf(borders + diffs + headers + align)
                sheetProcrank.write(rowIndex + 1, colIndex + 1, procrank[rowIndex][colIndex], xf)

        sheetProcrank.col(1).width = 7000
        sheetProcrank.col(2).width = 3000
        sheetProcrank.col(3).width = 4000
        sheetProcrank.col(4).width = 4000
        sheetProcrank.col(5).width = 4000
        sheetProcrank.col(6).width = 4000
        sheetProcrank.col(7).width = 4000

        save = None
        if output == None:
            save = 'Memory Compare %s' % datetime.datetime.now().strftime("%Y-%m-%d")
        else:
            if output.endswith(('.xls', '.XLS', '.pdf', '.PDF')):
                save = output[:-4]
            else:
                save = output
        print save
        xlsBook.save(save + '.xls')

class PDFGen(object):
    Date = datetime.datetime.now().strftime("%Y-%m-%d")
    FileLeft = None
    FileRight = None

    (PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize
    Styles = getSampleStyleSheet()

    def drawCoverPage(self, canvas, doc):
        title = 'Memory Compare'
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 220, title)
        canvas.setFont('Helvetica', 12)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 250, 'File A: ' + self.FileLeft)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 280, 'File B: ' + self.FileRight)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0 + 100, self.PAGE_HEIGHT - 310, self.Date)
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawContentPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawMeminfo(self, data):
        t = Table(data, None, None, None, 1, 1, 1)
        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                               ('BACKGROUND', (-1, 1), (-1, -1), colors.lightgreen),
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
        t = Table(data, None, None, None, 1, 1, 1)
        styles = []
        for i in range(len(data)):
            if i !=0 and i % 3 == 1:
                styles.append(('BOX', (0, i), (0, i + 2), 1, colors.black))
                styles.append(('BACKGROUND', (1, i+2), (-1, i+2), colors.lightgreen))

        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('GRID', (1, 0), (-1, -1), 1, colors.black),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (-1, 0), 2, colors.black),
                               ('LINEBELOW', (0, 'splitlast'), (1, 'splitlast'), 1, colors.black),
                               ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ] + styles
                               ))
        return t

    def generate(self, meminfo, procrank, fileLeft, fileRight, output=None):
        self.FileLeft = fileLeft
        self.FileRight = fileRight
        save = None
        if output == None:
            save = 'Memory Compare %s' % self.Date
        else:
            if output.endswith(('.pdf', '.PDF', '.xls', '.XLS')):
                save = output[:-4]
            else:
                save = output
        doc = SimpleDocTemplate(save + '.pdf')
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

        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)

def _Main(argv):
    opt_parser = optparse.OptionParser("%prog [options] file1 file2")
    opt_parser.add_option('-m', '--meminfo', action='store_true', dest='meminfo', default=False,
        help='Compare two meminfo files')
    opt_parser.add_option('-p', '--procrank', action="store_true", dest="procrank", default=False,
        help='Compare two procrank files')
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
