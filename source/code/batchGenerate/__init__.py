from AppKit import *
import os
import time

from vanilla import *

from lib.settings import doodleSupportedExportFileTypes

from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import RFont

from batchTools import settingsIdentifier, Report, buildTree


class BatchGenerate(Group):

    generateSettings = ["Decompose", "Remove Overlap", "Autohint", "Release Mode"]

    def __init__(self, posSize, controller):
        super(BatchGenerate, self).__init__(posSize)
        self.controller = controller

        y = 10
        for setting in self.generateSettings:
            key = setting.replace(" ", "_").lower()
            checkbox = CheckBox((10, y, -10, 22), setting,
                                value=getExtensionDefault("%s.%s" % (settingsIdentifier, key), True),
                                sizeStyle="regular",
                                callback=self.saveDefaults)
            setattr(self, key, checkbox)
            y += 24

        x = 10
        y += 10
        for format in doodleSupportedExportFileTypes:
            checkbox = CheckBox((x, y, 55, 22), format.upper(),
                                value=getExtensionDefault("%s.%s" % (settingsIdentifier, format), format != "pfa"),
                                callback=self.saveDefaults)
            setattr(self, format, checkbox)
            x += 55

        y += 32
        middle = 45
        self.suffixText = TextBox((10, y + 2, middle, 22), "Suffix:", alignment="right")
        self.generateSuffix = EditText((middle + 15, y, 100, 22),
            getExtensionDefault("%s.generateSuffix" % settingsIdentifier, ""),
            callback=self.saveDefaults)
        y += 30

        self.generate = Button((-100, -35, -10, 22), "Generate", callback=self.generateCallback)
        self.height = y + 5

    def saveDefaults(self, sender):
        for setting in self.generateSettings:
            key = setting.replace(" ", "_").lower()
            value = getattr(self, key).get()
            setExtensionDefault("%s.%s" % (settingsIdentifier, key), value)

        for format in doodleSupportedExportFileTypes + ["generateSuffix"]:
            value = getattr(self, format).get()
            setExtensionDefault("%s.%s" % (settingsIdentifier, format), value)

    def run(self, destDir, progress, report=None):
        paths = self.controller.get()

        decompose = self.decompose.get()
        removeOverlap = self.remove_overlap.get()
        autohint = self.autohint.get()
        releaseMode = self.release_mode.get()
        suffix = self.generateSuffix.get()
        suffix = time.strftime(suffix)

        formats = [i for i in doodleSupportedExportFileTypes if getattr(self, i).get()]

        if report is None:
            report = Report()
        report.writeTitle("Batch Generated Fonts:")
        report.newLine()

        progress.update("Collecting Data...")

        fonts = []
        for path in paths:
            font = RFont(path, document=False, showInterface=False)
            # check font info
            requiredFontInfo = dict(descender=-250, xHeight=500, ascender=750, capHeight=750, unitsPerEm=1000)
            for attr, value in requiredFontInfo.items():
                existingValue = getattr(font.info, attr)
                if existingValue is None:
                    setattr(font.info, attr, value)
            fonts.append(font)

        if decompose:
            report.writeTitle("Decompose:")
            report.indent()
            progress.update("Decompose...")
            progress.setTickCount(len(fonts))
            for font in fonts:
                report.write("%s %s" % (font.info.familyName, font.info.styleName))
                progress.update()
                font.decompose()
            progress.setTickCount(None)
            report.dedent()
            report.newLine()
            decompose = False

            if removeOverlap:
                report.writeTitle("Remove Overlap:")
                progress.update("Remove Overlap...")
                report.indent()
                progress.setTickCount(len(fonts))
                for font in fonts:
                    report.write("%s %s" % (font.info.familyName, font.info.styleName))
                    progress.update()
                    font.removeOverlap()
                progress.setTickCount(None)
                report.dedent()
                report.newLine()
                removeOverlap = False

        report.writeTitle("Generate:")
        exportPaths = []
        for index, font in enumerate(fonts):
            report.writeTitle((os.path.basename(paths[index])))
            report.newLine()
            report.write("source: %s" % paths[index])
            report.newLine()
            for format in formats:
                report.writeTitle("Generate %s" % format, "'")
                report.indent()
                familyName = font.info.familyName or "familyName-%s" % index
                familyName = familyName.replace(" ", "")
                styleName = font.info.styleName or "styleName-%s" % index
                styleName = styleName.replace(" ", "")
                if not self.controller.keepFileNames():
                    fileName = "%s-%s%s.%s" % (familyName, styleName, suffix, format)
                else:
                    fileName = os.path.basename(paths[index])
                    fileName, _ = os.path.splitext(fileName)
                    fileName = "%s%s.%s" % (fileName, suffix, format)
                progress.update("Generating ... %s" % fileName)
                if self.controller.exportInFolders():
                    fontDir = os.path.join(destDir, format)
                else:
                    fontDir = destDir
                buildTree(fontDir)
                path = os.path.join(fontDir, fileName)
                report.write("path: %s" % path)
                result = font.generate(path=path, format=format,
                              decompose=decompose,
                              checkOutlines=removeOverlap,
                              autohint=autohint,
                              releaseMode=releaseMode,
                              progressBar=progress,
                              glyphOrder=font.glyphOrder)
                report.indent()
                report.write(result)
                report.dedent()
                exportPaths.append(path)
                report.dedent()
                report.newLine()
            if not font.hasInterface():
                font.close()
        reportPath = os.path.join(destDir, "Batch Generate Report.txt")
        report.save(reportPath)
        return exportPaths

    def _generate(self, destDir):
        if not destDir:
            return
        destDir = destDir[0]
        self.controller.runTask(self.run, destDir=destDir)

    def generateCallback(self, sender):
        if not self.controller.hasSourceFonts("No Fonts to Generate.", "Add Open, drop or add Open Fonts fonts to batch them."):
            return
        self.controller.showGetFolder(self._generate)
