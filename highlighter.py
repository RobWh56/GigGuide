# highlighter.py:
# -- coding: utf-8 --
import re, gigguide
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets



class HighlightingRule:


    pass


class Highlighter(QtGui.QSyntaxHighlighter):


    def __init__(self, completer, parent=None):
        super(Highlighter, self).__init__(parent)

        self.highlightingRules = []

        bandrules = completer.bigdictionary["bandnamelist"]
        for key, value in bandrules.items():
            self.addHighlightRule(key, "bandnamelist")

        venuerules = completer.bigdictionary["venuenamelist"]
        for key, value in venuerules.items():
            self.addHighlightRule(key, "venuenamelist")


    def addHighlightRule(self, key, ruletype):
        if ruletype == "bandnamelist":
            colour = QtCore.Qt.blue
        elif ruletype == "venuenamelist":
            colour = QtCore.Qt.magenta
        newrule = HighlightingRule()
        newruleformat = QtGui.QTextCharFormat()
        newruleformat.setForeground(colour)
        newruleformat.setFontWeight(QtGui.QFont.Normal)
        newrule.format = newruleformat
        newrule.pattern = re.compile(key)
        self.highlightingRules.append(newrule)


    def highlightBlock(self, text):
            # debug print("- " + text[0:20])
            for rule in self.highlightingRules:
                s = rule.pattern.search(text)
                if s:
                    index = s.start()
                else:
                    index = -1
                while index >= 0:
                    length = s.end() - s.start()
                    #print("- " + "{:<20}".format(text) + " index: " + str(index) + "length: " + str(length) + " pattern: " + s.group())
                    self.setFormat(index, length, rule.format)
                    #index = rule.pattern.indexIn(text, index + length)
                    s = rule.pattern.search(text, index + length)
                    if s:
                        index = s.start()
                    else:
                        index = -1
                    self.setCurrentBlockState(0)
