#!/usr/bin/python

import sys
import optparse
import datetime
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.tables import TableStyle
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize
from reportlab.lib.styles import ParagraphStyle
#from xlwt import Workbook, easyxf

Styles = {'Normal': ParagraphStyle(name = 'Normal', fontName = 'Helvetica', fontSize = 10, leading = 12),
          'Tips': ParagraphStyle(name = 'Tips', fontName = 'Helvetica', fontSize = 8, leading = 12),
          'Heading1': ParagraphStyle(name = 'Heading1', fontName = 'Helvetica-Bold', fontSize = 18, leading = 22, spaceAfter = 6),
          'Heading2': ParagraphStyle(name = 'Heading2', fontName = 'Helvetica', fontSize = 12, leading = 12),}

class InputInfo(object):
    Free = {'MemFree': 1, 'Cached': 1, 'SwapCached': 1, 'Mlocked': -1, 'Shmem': -1}
    Used = ['AnonPages', 'Slab', 'VmallocAlloc', 'Mlocked', 'Shmem', 'KernelStack', 'PageTables', 'KGSL_ALLOC', 'ION_ALLOC', 'ION_Alloc']
    SwapUsage = {'SwapTotal': 1, 'SwapFree': -1}
    LMKFile = {'Cached': 1, 'Buffers': 1, 'SwapCached': 1, 'Mlocked': -1, 'Shmem': -1}
    Rams = {512: ((20, 50, 200), (2, 5, 20)), 768: ((20, 50, 200), (2, 5, 20)), 1024: ((50, 100, 500), (5, 10, 50)), 2048: ((50, 100, 500), (5, 10, 50))}

    def __init__(self, filePath):
        self.meminfo = {}
        self.procrank = {}
        self.filePath = filePath
        self.ram = 0
        self._parse()

    def _parse(self):
        fileObject = open(self.filePath, 'r').read()
        lines = fileObject.split('\n')
        startM = False
        startP = False
        for line in lines:
            ram = re.search("(?<=RAM: )\d+(?=K)", line)
            if ram != None and self.ram == 0:
                self.ram = reduce(lambda x, y: y if x <= (int(ram.group()) / 1000) and y > (int(ram.group()) / 1000) else x, self.Rams.keys())
            if not startM and not startP:
                if re.search('MemTotal', line) != None: startM = True
                elif re.search("^\s*\d+(\s+\d+K){4}", line) != None: startP = True
                else: continue
            formated = line.split()
            if startM:
                if len(formated) == 0:
                    startM = False
                    if len(self.procrank): break
                    else: continue
                self.meminfo[formated[0][:-1]] = int(formated[1])
                if formated[0][:-1] == 'MemTotal' and self.ram == 0:
                    self.ram = reduce(lambda x, y: y if x <= (int(formated[1]) / 1000) and y > (int(formated[1]) / 1000) else x, self.Rams.keys())
            if startP:
                if re.search("^\s*\d+(\s+\d+K){4}", line) == None:
                    startP = False
                    if len(self.meminfo): break
                    else: continue
                self.procrank[formated[-1]] = [int(value[:-1]) for value in formated[1:-1]]
        if len(self.meminfo):
            self.meminfo['Free'] = reduce(lambda x, y: x + y, [self.meminfo[value] * self.Free[value] for value in filter(lambda x: self.meminfo.has_key(x), self.Free.keys())])
            self.meminfo['Used'] = reduce(lambda x, y: x + y, [self.meminfo[value] for value in filter(lambda x: self.meminfo.has_key(x), self.Used)])
            self.meminfo['SwapUsage'] = reduce(lambda x, y: x + y, [self.meminfo[value] * self.SwapUsage[value] for value in filter(lambda x: self.meminfo.has_key(x), self.SwapUsage.keys())])
            self.meminfo['LMK File'] = reduce(lambda x, y: x + y, [self.meminfo[value] * self.LMKFile[value] for value in filter(lambda x: self.meminfo.has_key(x), self.LMKFile.keys())])

class Compare(object):
    MeminfoSummary = ['Free', 'MemFree', 'Cached', 'SwapCached', 'Used', 'AnonPages', 'Slab', 'Buffers', 'Mlocked', 'Shmem', 'KernelStack', 'PageTables', 'VmallocAlloc', 'KGSL_ALLOC', 'ION_Alloc', 'ION_ALLOC', 'SwapUsage', 'LMK File']
    MeminfoFull = ['MemTotal', 'MemFree', 'Buffers', 'Cached', 'SwapCached', 'Active', 'Inactive', 'Active(anon)', 'Inactive(anon)', 'Active(file)', 'Inactive(file)', 'Unevictable', 'Mlocked', 'HighTotal', 'HighFree', 'LowTotal', 'LowFree', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback', 'AnonPages', 'Mapped', 'Shmem', 'Slab', 'SReclaimable', 'SUnreclaim', 'KernelStack', 'PageTables', 'NFS_Unstable', 'Bounce', 'WritebackTmp', 'CommitLimit', 'Committed_AS', 'VmallocTotal', 'VmallocUsed', 'VmallocIoRemap', 'VmallocAlloc', 'VmallocMap', 'VmallocUserMap', 'VmallocVpage', 'VmallocChunk', 'KGSL_ALLOC', 'ION_ALLOC']

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def mTable(self, items):
        return [['Item (MB)', 'A', 'B', 'Diff']] + [[item,
                '%.1f' % (self.left.meminfo[item] / 1000.0) if self.left.meminfo.has_key(item) else '-',
                '%.1f' % (self.right.meminfo[item] / 1000.0) if self.right.meminfo.has_key(item) else '-',
                '%.1f' % ((self.left.meminfo[item] - self.right.meminfo[item]) / 1000.0) if self.left.meminfo.has_key(item) and self.right.meminfo.has_key(item) else '-']
                for item in filter(lambda x: self.left.meminfo.has_key(x) or self.right.meminfo.has_key(x), items)]

    def pTable(self, items):
        return [['PSS (MB)', 'A', 'B', 'Diff']] + [[item,
                '%.1f' % (self.left.procrank[item][2] / 1000.0) if self.left.procrank.has_key(item) else '-',
                '%.1f' % (self.right.procrank[item][2] / 1000.0) if self.right.procrank.has_key(item) else '-',
                '%.1f' % ((self.left.procrank[item][2] - self.right.procrank[item][2]) / 1000.0) if self.left.procrank.has_key(item) and self.right.procrank.has_key(item) else '-']
                for item in sorted(filter(lambda x: self.left.procrank.has_key(x) or self.right.procrank.has_key(x), items), key=lambda x: self.left.procrank[x][2] if self.left.procrank.has_key(x) else self.right.procrank[x][2], reverse=True)]

    def pTopDiff(self, reverse):
        return ['%s: %.1f MB' % (proc, (1 if reverse else -1) * (self.left.procrank[proc][2] - self.right.procrank[proc][2]) / 1000.0) for proc in sorted(set(self.left.procrank.keys()) & set(self.right.procrank.keys()), key=lambda x: self.left.procrank[x][2] - self.right.procrank[x][2], reverse=reverse)[:5]]

    def pLeftOnly(self):
        return ['%s: %.1f MB' % (proc, self.left.procrank[proc][2] / 1000.0) for proc in (set(self.left.procrank.keys()) - set(self.right.procrank.keys()))]

    def pRightOnly(self):
        return ['%s: %.1f MB' % (proc, self.right.procrank[proc][2] / 1000.0) for proc in (set(self.right.procrank.keys()) - set(self.left.procrank.keys()))]

#class XLSGen(object):
#    VMinBorders = 'top medium, bottom medium,'
#    VMaxBorders = 'top thin, bottom medium,'
#    VMidBorders = 'top thin, bottom thin,'
#    HMinBorders = 'left medium, right thin,'
#    HMaxBorders = 'left thin, right medium,'
#    HMidBorders = 'left thin, right thin,'
#
#    def generate(self, compare, output=None):
#        xlsBook = Workbook()
#        if len(meminfo) != 0:
#            sheetMeminfo = xlsBook.add_sheet('MEMINFO SUMMARY')
#            for rowIndex in range(len(compare.mTable(compare.MeminfoSummary))):
#                for colIndex in range(len(compare.mTable(compare.MeminfoSummary)[0])):
#                    borders = 'borders: '
#                    headers = ''
#                    align = ''
#                    if rowIndex == 0:
#                        headers = 'pattern: pattern solid, fore_colour green;'
#                        borders = borders + self.VMinBorders
#                    else:
#                        if rowIndex == (len(compare.mTable(compare.MeminfoSummary)) - 1):
#                            borders = borders + self.VMaxBorders
#                        else:
#                            borders = borders + self.VMidBorders
#                    if colIndex == 0:
#                        borders = borders + self.HMinBorders
#                    else:
#                        align = 'alignment: horizontal right;'
#                        if colIndex == (len(compare.mTable(compare.MeminfoSummary)[0]) - 1):
#                            borders = borders + self.HMaxBorders
#                        else:
#                            borders = borders + self.HMidBorders
#                    borders = borders + ';'
#                    xf = easyxf(borders + headers + align)
#                    sheetMeminfo.write(rowIndex + 1, colIndex + 1, compare.mTable(compare.MeminfoSummary)[rowIndex][colIndex], xf)
#            for i in range(1,5):
#                sheetMeminfo.col(i).width = 5000
#
#        if len(procrank) != 0:
#            sheetProcrank = xlsBook.add_sheet('PROCRANK')
#            for rowIndex in range(len(procrank)):
#                for colIndex in range(len(procrank[0])):
#                    borders = 'borders: '
#                    headers = ''
#                    diffs = ''
#                    align = ''
#                    if rowIndex == 0:
#                        headers = 'pattern: pattern solid, fore_colour green;'
#                        borders = borders + self.VMinBorders
#                    else:
#                        if rowIndex == (len(procrank) - 1) and colIndex != 0:
#                            borders = borders + self.VMaxBorders
#                        else:
#                            if colIndex != 0:
#                                borders = borders + self.VMidBorders
#                    if colIndex == 0:
#                        if rowIndex % 3 == 1 and rowIndex != (len(procrank) - 1):
#                            borders = 'borders: top thin,'
#                        else:
#                            if rowIndex and rowIndex % 3 == 0 and rowIndex != (len(procrank) - 1):
#                                borders = 'borders: bottom thin,'
#                            else:
#                                if rowIndex and rowIndex != (len(procrank) - 1):
#                                    borders = 'borders: '
#                                else:
#                                    if rowIndex == 0:
#                                        borders = 'borders: top medium, bottom medium,'
#                                    else:
#                                        borders = 'borders: bottom medium,'
#                        borders = borders + self.HMinBorders
#                    else:
#                        align = 'alignment: horizontal right;'
#                        if rowIndex and rowIndex % 3 ==0:
#                            diffs = 'pattern: pattern solid, fore_colour light_green;'
#                        if colIndex == (len(procrank[0]) - 1):
#                            borders = borders + self.HMaxBorders
#                        else:
#                            borders = borders + self.HMidBorders
#                    borders = borders + ';'
#                    xf = easyxf(borders + diffs + headers + align)
#                    sheetProcrank.write(rowIndex + 1, colIndex + 1, procrank[rowIndex][colIndex], xf)
#            sheetProcrank.col(1).width = 7000
#            sheetProcrank.col(2).width = 3000
#            sheetProcrank.col(3).width = 4000
#            sheetProcrank.col(4).width = 4000
#            sheetProcrank.col(5).width = 4000
#            sheetProcrank.col(6).width = 4000
#            sheetProcrank.col(7).width = 4000
#
#        save = None
#        if output == None:
#            save = 'Memory Compare %s' % datetime.datetime.now().strftime("%Y-%m-%d")
#        else:
#            if output.endswith(('.xls', '.XLS', '.pdf', '.PDF')):
#                save = output[:-4]
#            else:
#                save = output
#        xlsBook.save(save + '.xls')

class PDFGen(object):
    Date = datetime.datetime.now().strftime("%Y-%m-%d")

    (PAGE_WIDTH, PAGE_HEIGHT) = defaultPageSize

    def drawCoverPage(self, canvas, doc):
        title = 'Memory Compare'
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0, self.PAGE_HEIGHT - 220, title)
        canvas.setFont('Helvetica', 12)
        canvas.drawCentredString(self.PAGE_WIDTH / 2.0 + 100, self.PAGE_HEIGHT - 280, self.Date)
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawContentPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def drawTable(self, data):
        t = Table(data, None, None, None, 1, 1, 1)
        extraStyle = []
        for i in range(len(data[1:])):
            if data[1:][i][-1] != '-':
                extraStyle.append(('TEXTCOLOR', (-1, i + 1), (-1, i + 1), colors.blue if float(data[1:][i][-1]) >= 0 else colors.red))
            if data[1:][i][0] == 'Free' or data[1:][i][0] == 'Used':
                extraStyle.append(('BACKGROUND', (0, i + 1), (-1, i + 1), colors.orange))
            if data[1:][i][0] == 'SwapUsage' or data[1:][i][0] == 'LMK File':
                extraStyle.append(('BACKGROUND', (0, i + 1), (-1, i + 1), colors.lightgreen))

        t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.deepskyblue),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (-1, 0), 2, colors.black),
                               ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ] + extraStyle))
        t.hAlign = 'LEFT'
        return t

    def generate(self, compare, fileLeft, fileRight, output=None):
        save = None
        if output == None:
            save = 'Memory Compare %s' % self.Date
        else:
            if output.endswith(('.pdf', '.PDF', '.xls', '.XLS')):
                save = output[:-4]
            else:
                save = output
        doc = SimpleDocTemplate(save + '.pdf')
        story = [Spacer(1, 1.7 * inch)]
        story.append(PageBreak())

        if len(compare.left.meminfo) > 0 or len(compare.right.meminfo) > 0:
            story.append(Paragraph('MemInfo Compare', Styles['Heading1']))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph('A: %s' % fileLeft, Styles['Normal']))
            story.append(Paragraph('B: %s' % fileRight, Styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('<u>Summary</u>', Styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(self.drawTable(compare.mTable(compare.MeminfoSummary)))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('* Free = MemFree + Cached + SwapCached - Mlocked - Shmem', Styles['Tips']))
            story.append(Paragraph('* Used = AnonPages + Slab + VmallocAlloc + Mlocked + Shmem + KernelStack + PageTables + KGSL_ALLOC + ION_ALLOC', Styles['Tips']))
            story.append(Paragraph('* SwapUsage = SwapTotal - SwapFree', Styles['Tips']))
            story.append(Paragraph('* LMK File = Cached + Buffers + SwapCached - Mlocked - Shmem', Styles['Tips']))
            story.append(PageBreak())
            story.append(Paragraph('<u>Full data</u>', Styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(self.drawTable(compare.mTable(compare.MeminfoFull)))
            story.append(PageBreak())

        if len(compare.left.procrank) > 0 and len(compare.right.procrank) > 0:
            story.append(Paragraph('Procrank Compare', Styles['Heading1']))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph('A: %s' % fileLeft, Styles['Normal']))
            story.append(Paragraph('B: %s' % fileRight, Styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('<u>Summary</u>', Styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('A > B Top 5 process', Styles['Normal'], '*'))
            story.append(Spacer(1, 0.1 * inch))
            for i in range(len(compare.pTopDiff(True))):
                text = Paragraph('%s' % compare.pTopDiff(True)[i], Styles['Normal'], '%d' % (i + 1))
                story.append(text)
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('B > A Top 5 process', Styles['Normal'], '*'))
            story.append(Spacer(1, 0.1 * inch))
            for i in range(len(compare.pTopDiff(False))):
                text = Paragraph('%s' % compare.pTopDiff(False)[i], Styles['Normal'], '%d' % (i + 1))
                story.append(text)
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('Process in A only', Styles['Normal'], '*'))
            story.append(Spacer(1, 0.1 * inch))
            for i in range(len(compare.pLeftOnly())):
                text = Paragraph('%s' % compare.pLeftOnly()[i], Styles['Normal'], '%d' % (i + 1))
                story.append(text)
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph('Process in B only', Styles['Normal'], '*'))
            story.append(Spacer(1, 0.1 * inch))
            for i in range(len(compare.pRightOnly())):
                text = Paragraph('%s' % compare.pRightOnly()[i], Styles['Normal'], '%d' % (i + 1))
                story.append(text)
            story.append(PageBreak())
            story.append(Paragraph('<u>Full data</u>', Styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(self.drawTable(compare.pTable(compare.left.procrank.keys())))

        doc.build(story, onFirstPage=self.drawCoverPage, onLaterPages=self.drawContentPage)

def _Main(argv):
    opt_parser = optparse.OptionParser("%prog [options] file1 file2")
    opt_parser.add_option('-o', '--output', dest='output',
        help='Use <FILE> to store the generated report', metavar='FILE')
    (opts, args) = opt_parser.parse_args(argv)

    if len(args) != 2:
        opt_parser.print_help()
        sys.exit(1)
    else:
        left = InputInfo(args[0])
        right = InputInfo(args[1])
        compare = Compare(left, right)
        pdf = PDFGen()
        pdf.generate(compare, left.filePath, right.filePath, opts.output)

if __name__ == '__main__':
    _Main(sys.argv[1:])
