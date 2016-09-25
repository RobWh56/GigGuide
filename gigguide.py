# -*- coding: utf-8 -*-

import sys, copy, highlighter, re, os, shutil
from datetime import datetime, timedelta

# PYQT5 PyQt4’s QtGui module has been split into PyQt5’s QtGui, QtPrintSupport and QtWidgets modules

from PyQt5 import QtWidgets
# PYQT5 QMainWindow, QApplication, QAction, QFontComboBox, QSpinBox, QTextEdit, QMessageBox
# PYQT5 QFileDialog, QColorDialog, QDialog

from PyQt5 import QtPrintSupport
# PYQT5 QPrintPreviewDialog, QPrintDialog

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt

from ext import find
from os import path

DEFAULTDIRECTORY = os.getcwd()
if sys.platform == 'win32':
    FILEMARKER = "\\"
elif sys.platform == 'linux':
    FILEMARKER = "/"
else:
    print("unknown platorm =" + sys.platform + " currently only setup for windows and linux")
    sys.exit(app.exec_())
DEFAULTDIRECTORY = DEFAULTDIRECTORY + FILEMARKER
DEFAULTDICTDIRECTORY = DEFAULTDIRECTORY + "Dictionaries" + FILEMARKER
DEFAULTGUIDEDIRECTORY = DEFAULTDIRECTORY + "testdata" + FILEMARKER
DEFAULTEXPORTDIRECTORY = DEFAULTDIRECTORY + "testdata" + FILEMARKER

PREFERENCES = {"bandnamelist": DEFAULTDICTDIRECTORY + "bands_comma_delimited.txt",
               "venuenamelist": DEFAULTDICTDIRECTORY + "venues_comma_delimited.txt",
               "urllist": DEFAULTDICTDIRECTORY + "urls_comma_delimited.txt"}

SAVE = 1
DISCARD = 2
CANCEL = 3
SYSTEMNAME = "Brisbane Live Music Guide"


class MyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyDialog, self).__init__(parent)

        #self.buttonBox = QtWidgets.QDialogButtonBox(self)
        #self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        #self.buttonBox.setFixedSize(700, 50)
        #self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        #self.buttonBox.setWindowTitle(SYSTEMNAME)
        self.textBrowser = QtWidgets.QTextBrowser(self)
        self.textBrowser.setFixedSize(700, 500)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.textBrowser)
        self.setWindowTitle("HTML View equivalent to Export (which is RTF)")
        #self.verticalLayout.addWidget(self.buttonBox)


class MyPlainTextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def insertCompletion(self, completion):
        print("insertCompletion invoked")
        tc = self.textCursor()
        for i in self.completer.completionPrefix():
            tc.deletePreviousChar()
        tc.insertText(completion)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        statusbarmsg = "textUnderCursor invoked"
        print("textUnderCursor")
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, event):
        statusbarmsg = "focusInEvent invoked"
        print("focusInEvent")
        if self.completer:
            self.completer.setWidget(self)
        QtWidgets.QPlainTextEdit.focusInEvent(self, event)

    def autocomplete(self):
        statusbarmsg = "autocomplete invoked"
        print("autocomplete")

        currentfiletypewas = self.completer.currentfiletype
        thiscursor = self.textCursor()
        thisdocument = self.toPlainText()
        cursorposition = thiscursor.position()
        foundplace = False
        poke = cursorposition - 1
        while not foundplace:
            if poke == -1:
                self.completer.currentfiletype = ""
                return
            elif thisdocument[poke] in ["/n", ':']:
                self.completer.currentfiletype = ""
                return
            elif thisdocument[poke] == "{":
                self.completer.currentfiletype = "venuenamelist"
                foundplace = True
            elif thisdocument[poke] == "[":
                self.completer.currentfiletype = "bandnamelist"
                foundplace = True
            poke = poke - 1
        if self.completer.currentfiletype:
            if currentfiletypewas != self.completer.currentfiletype:
                self.completer.changeModel(self.completer.currentfiletype)

            # print ("at:" + str(cursorposition) + " in length:" + str(len(thisdocument)))
            eow = """~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="""  # end of word
            # has modifier is true if the key has a modifier (and false if no modifier)
            completionPrefix = self.textUnderCursor()

            # if the word currently under the cursor is different from the search word in the completer
            # update the search word in the prefix and update the completer popup box contents
            if (completionPrefix != self.completer.completionPrefix()):
                self.completer.setCompletionPrefix(completionPrefix)
                popup = self.completer.popup()
                popup.setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
            # setup a popup box to fit the text offered by the completer
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            # pop it up
            self.completer.complete(cr)

    def keyPressEvent(self, event):
        # "DEBUG STUFF"
        # statusbarmsg = "keyPressEvent invoked"
        if self.completer:
            selfcompleter = "true"
        else:
            selfcompleter = "false"
        print("keyPressEvent self.completer=" + selfcompleter + " event.key()=" + str(event.key()) +
              " event.text() =" + event.text() + " self.textUnderCursor()=" + self.textUnderCursor() +
              " self.completer.completionPrefix()=" + self.completer.completionPrefix())
        # if the text completer has text to offer,  the popup is visible and user has typed a finishing key, return
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (
                    QtCore.Qt.Key_Enter,
                    QtCore.Qt.Key_Return,
                    QtCore.Qt.Key_Escape,
                    QtCore.Qt.Key_Tab,
                    QtCore.Qt.Key_Backtab):
                event.ignore()
                return
        currentfiletypewas = self.completer.currentfiletype
        thiscursor = self.textCursor()
        thisdocument = self.toPlainText()
        cursorposition = thiscursor.position()
        foundplace = False
        poke = cursorposition - 1
        while not foundplace:
            if poke == -1:
                self.completer.currentfiletype = ""
                foundplace = True
            elif thisdocument[poke] in ["/n", ":"]:
                self.completer.currentfiletype = ""
                foundplace = True
            elif thisdocument[poke] == "{":
                self.completer.currentfiletype = "venuenamelist"
                foundplace = True
            elif thisdocument[poke] == "[":
                self.completer.currentfiletype = "bandnamelist"
                foundplace = True
            poke = poke - 1


        if self.completer.currentfiletype:
            if currentfiletypewas != self.completer.currentfiletype:
                self.completer.changeModel(self.completer.currentfiletype)
        ## has ctrl-G been pressed??
        isShortcut = (
            QtCore.Qt.ControlModifier == event.modifiers() and (event.key() == QtCore.Qt.Key_G))
        # if not both text offered by completer and shortcut, advise completer of event
        if not (self.completer and isShortcut):
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

        ## ctrl or shift key on it's own??
        ctrlOrShift = event.modifiers() in (QtCore.Qt.ControlModifier,
                                            QtCore.Qt.ShiftModifier)
        # if just control or shift without actual key, return
        if ctrlOrShift and not event.text():
            # ctrl or shift key on it's own
            return
        # AttributeError: module 'PyQt5.QtCore' has no attribute 'QString'
        # eow = QtCore.QString("~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-=") #end of word
        eow = """~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="""  # end of word
        # has modifier is true if the key has a modifier (and false if no modifier)
        hasModifier = ((event.modifiers() != QtCore.Qt.NoModifier) and
                       not ctrlOrShift)
        # completionPrefix set to contain the word currently under the cursor
        completionPrefix = self.textUnderCursor()

        # if not the official shortcut, and modifier only or unmodified character only, then return
        # also if the number of characters in current word is less than 3 then return
        # also if the rightmost character of the word is non alphabetic then return
        # .. in each case hide any visible popup before returning
        if (not isShortcut and (hasModifier or not event.text() or
                                        len(completionPrefix) < 3 or
                                # AttributeError: 'str' object has no attribute 'contains'
                                # AttributeError: 'str' object has no attribute 'right'
                                # eow.contains(event.text().right(1)))):
                                        event.text()[-1:] in eow)):
            self.completer.popup().hide()
            return
        # if the word currently under the cursor is different from the search word in the completer
        # update the search word in the prefix and update the completer popup box contents
        if (completionPrefix != self.completer.completionPrefix()):
            self.completer.setCompletionPrefix(completionPrefix)
            popup = self.completer.popup()
            popup.setCurrentIndex(
                self.completer.completionModel().index(0, 0))
        # setup a popup box to fit the text offered by the completer
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                    + self.completer.popup().verticalScrollBar().sizeHint().width())
        # pop it up
        self.completer.complete(cr)


class DictionaryCompleter(QtWidgets.QCompleter):
    # DictionaryCompleter objects inherit methods and attributes from QtWidgets.QCompleter
    # object containing attrubute words which is python string containing dictionary opened from file
    def __init__(self, parent=None):
        QtWidgets.QCompleter.__init__(self)
        self.words = dict()
        self.bigdictionary = dict()
        self.currentfiletype = ""
        for filetype, filepath in PREFERENCES.items():
            dictn = dict()
            wrds = []
            try:
                f = open(filepath, "r")
                for word in f:
                    if len(word.strip()) > 0:
                        try:
                            key, value = word.split(',')
                        except ValueError:
                            key = word.strip()
                            value = ""
                            print("error on reading dictionary file - more or less than one comma on line =" + word +
                                  "dictionary has members" + str(len(dictn)))
                        else:
                            key = key.strip()
                            value = value.strip()
                        dictn[key] = value
                        wrds.append(key)
                print("dictionary has members" + str(len(dictn)))
                f.close()
            except IOError:
                statusbarmsg = "dictionary not in anticipated location"
                print(statusbarmsg)
            self.bigdictionary[filetype] = dictn.copy()
            self.words[filetype] = wrds[:]
        self.changeModel("bandnamelist")

    def changeModel(self, filetype):
        if filetype:
            wordlist = self.words[filetype]
            slmodel = QtCore.QStringListModel()
            slmodel.setStringList(wordlist)
            self.setModel(slmodel)
        self.currentfiletype = filetype


class Main(QtWidgets.QMainWindow):
    def __init__(self, completer, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.filename = ""
        self.statusbarmsg = ""
        self.statusbarmsgdisplay = True
        self.completer = completer

        self.changesSaved = True

        self.initUI()

    def initToolbar(self):

        self.newAction = QtWidgets.QAction(QtGui.QIcon("icons/new.png"), "New", self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.setStatusTip("Create a new document from scratch.")
        self.newAction.triggered.connect(self.new)

        self.openAction = QtWidgets.QAction(QtGui.QIcon("icons/open.png"), "Open file", self)
        self.openAction.setStatusTip("Open existing document")
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.open)

        self.saveAction = QtWidgets.QAction(QtGui.QIcon("icons/save.png"), "Save", self)
        self.saveAction.setStatusTip("Save document")
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.save)

        self.saveasAction = QtWidgets.QAction(QtGui.QIcon("icons/saveas.png"), "Save as..", self)
        self.saveasAction.setStatusTip("Save document as...")
        self.saveasAction.setShortcut("Ctrl+Shift+S")
        self.saveasAction.triggered.connect(self.saveas)

        self.exportAction = QtWidgets.QAction("Export", self)
        self.exportAction.setStatusTip("Export document to html")
        self.exportAction.setShortcut("Ctrl+L")
        self.exportAction.triggered.connect(self.export)

        self.printAction = QtWidgets.QAction(QtGui.QIcon("icons/print.png"), "Print document", self)
        self.printAction.setStatusTip("Print document")
        self.printAction.setShortcut("Ctrl+P")
        self.printAction.triggered.connect(self.printHandler)

        self.previewAction = QtWidgets.QAction(QtGui.QIcon("icons/preview.png"), "Page view", self)
        self.previewAction.setStatusTip("Preview page before printing")
        self.previewAction.setShortcut("Ctrl+Shift+P")
        self.previewAction.triggered.connect(self.preview)

        self.findAction = QtWidgets.QAction(QtGui.QIcon("icons/find.png"), "Find and replace", self)
        self.findAction.setStatusTip("Find and replace words in your document")
        self.findAction.setShortcut("Ctrl+F")
        self.findAction.triggered.connect(find.Find(self).show)

        self.cutAction = QtWidgets.QAction(QtGui.QIcon("icons/cut.png"), "Cut to clipboard", self)
        self.cutAction.setStatusTip("Delete and copy text to clipboard")
        self.cutAction.setShortcut("Ctrl+X")
        self.cutAction.triggered.connect(self.text.cut)

        self.copyAction = QtWidgets.QAction(QtGui.QIcon("icons/copy.png"), "Copy to clipboard", self)
        self.copyAction.setStatusTip("Copy text to clipboard")
        self.copyAction.setShortcut("Ctrl+C")
        self.copyAction.triggered.connect(self.text.copy)

        self.pasteAction = QtWidgets.QAction(QtGui.QIcon("icons/paste.png"), "Paste from clipboard", self)
        self.pasteAction.setStatusTip("Paste text from clipboard")
        self.pasteAction.setShortcut("Ctrl+V")
        self.pasteAction.triggered.connect(self.text.paste)

        self.undoAction = QtWidgets.QAction(QtGui.QIcon("icons/undo.png"), "Undo last action", self)
        self.undoAction.setStatusTip("Undo last action")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.text.undo)

        self.redoAction = QtWidgets.QAction(QtGui.QIcon("icons/redo.png"), "Redo last undone thing", self)
        self.redoAction.setStatusTip("Redo last undone thing")
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.triggered.connect(self.text.redo)

        self.venueAction = QtWidgets.QAction("Venue", self)
        self.venueAction.setStatusTip("switch to venue autocompletion")
        self.venueAction.setShortcut("Ctrl+M")
        # self.venueAction.triggered.connect(self.text.changeModel("venuenamelist"))

        wordCountAction = QtWidgets.QAction(QtGui.QIcon("icons/count.png"), "See word/symbol count", self)
        wordCountAction.setStatusTip("See word/symbol count")
        wordCountAction.setShortcut("Ctrl+W")
        wordCountAction.triggered.connect(self.wordCount)

        autocompleteAction = QtWidgets.QAction("Autocomplete...", self)
        autocompleteAction.setStatusTip("See word/symbol count")
        autocompleteAction.setShortcut("Ctrl+G")
        autocompleteAction.triggered.connect(self.text.autocomplete)

        self.addUrlAction = QtWidgets.QAction("add url...", self)
        self.addUrlAction.setStatusTip("Add band url to selected band name")
        self.addUrlAction.setShortcut("Ctrl+K")
        self.addUrlAction.triggered.connect(self.addUrl)

        # tableAction = QtWidgets.QAction(QtGui.QIcon("icons/table.png"),"Insert table",self)
        # tableAction.setStatusTip("Insert table")
        # tableAction.setShortcut("Ctrl+T")
        # tableAction.triggered.connect(table.Table(self).show)

        # imageAction = QtWidgets.QAction(QtGui.QIcon("icons/image.png"),"Insert image",self)
        # imageAction.setStatusTip("Insert image")
        # imageAction.setShortcut("Ctrl+Shift+I")
        # imageAction.triggered.connect(self.insertImage)

        # bulletAction = QtWidgets.QAction(QtGui.QIcon("icons/bullet.png"),"Insert bullet List",self)
        # bulletAction.setStatusTip("Insert bullet list")
        # bulletAction.setShortcut("Ctrl+Shift+B")
        # bulletAction.triggered.connect(self.bulletList)

        # numberedAction = QtWidgets.QAction(QtGui.QIcon("icons/number.png"),"Insert numbered List",self)
        # numberedAction.setStatusTip("Insert numbered list")
        # numberedAction.setShortcut("Ctrl+Shift+L")
        # numberedAction.triggered.connect(self.numberList)

        self.toolbar = self.addToolBar("Options")

        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)

        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveasAction)
        self.toolbar.addAction(self.exportAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.previewAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.cutAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.pasteAction)
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.findAction)
        # self.toolbar.addAction(dateTimeAction)
        self.toolbar.addAction(wordCountAction)
        self.toolbar.addAction(autocompleteAction)
        self.toolbar.addAction(self.addUrlAction)

        # self.toolbar.addAction(tableAction)
        # self.toolbar.addAction(imageAction)

        # self.toolbar.addSeparator()

        # self.toolbar.addAction(bulletAction)
        # self.toolbar.addAction(numberedAction)

        self.addToolBarBreak()

    # never called
    def initFormatbar(self):

        fontBox = QtWidgets.QFontComboBox(self)
        fontBox.currentFontChanged.connect(lambda font: self.text.setCurrentFont(font))

        fontSize = QtWidgets.QSpinBox(self)

        # Will display " pt" after each value
        fontSize.setSuffix(" pt")

        fontSize.valueChanged.connect(lambda size: self.text.setFontPointSize(size))

        fontSize.setValue(14)

        fontColor = QtWidgets.QAction(QtGui.QIcon("icons/font-color.png"), "Change font color", self)
        fontColor.triggered.connect(self.fontColorChanged)

        boldAction = QtWidgets.QAction(QtGui.QIcon("icons/bold.png"), "Bold", self)
        boldAction.triggered.connect(self.bold)

        italicAction = QtWidgets.QAction(QtGui.QIcon("icons/italic.png"), "Italic", self)
        italicAction.triggered.connect(self.italic)

        underlAction = QtWidgets.QAction(QtGui.QIcon("icons/underline.png"), "Underline", self)
        underlAction.triggered.connect(self.underline)

        strikeAction = QtWidgets.QAction(QtGui.QIcon("icons/strike.png"), "Strike-out", self)
        strikeAction.triggered.connect(self.strike)

        superAction = QtWidgets.QAction(QtGui.QIcon("icons/superscript.png"), "Superscript", self)
        superAction.triggered.connect(self.superScript)

        subAction = QtWidgets.QAction(QtGui.QIcon("icons/subscript.png"), "Subscript", self)
        subAction.triggered.connect(self.subScript)

        alignLeft = QtWidgets.QAction(QtGui.QIcon("icons/align-left.png"), "Align left", self)
        alignLeft.triggered.connect(self.alignLeft)

        alignCenter = QtWidgets.QAction(QtGui.QIcon("icons/align-center.png"), "Align center", self)
        alignCenter.triggered.connect(self.alignCenter)

        alignRight = QtWidgets.QAction(QtGui.QIcon("icons/align-right.png"), "Align right", self)
        alignRight.triggered.connect(self.alignRight)

        alignJustify = QtWidgets.QAction(QtGui.QIcon("icons/align-justify.png"), "Align justify", self)
        alignJustify.triggered.connect(self.alignJustify)

        indentAction = QtWidgets.QAction(QtGui.QIcon("icons/indent.png"), "Indent Area", self)
        indentAction.setShortcut("Ctrl+Tab")
        indentAction.triggered.connect(self.indent)

        dedentAction = QtWidgets.QAction(QtGui.QIcon("icons/dedent.png"), "Dedent Area", self)
        dedentAction.setShortcut("Shift+Tab")
        dedentAction.triggered.connect(self.dedent)

        backColor = QtWidgets.QAction(QtGui.QIcon("icons/highlight.png"), "Change background color", self)
        backColor.triggered.connect(self.highlight)

        self.formatbar = self.addToolBar("Format")

        self.formatbar.addWidget(fontBox)
        self.formatbar.addWidget(fontSize)

        self.formatbar.addSeparator()

        self.formatbar.addAction(fontColor)
        self.formatbar.addAction(backColor)

        self.formatbar.addSeparator()

        self.formatbar.addAction(boldAction)
        self.formatbar.addAction(italicAction)
        self.formatbar.addAction(underlAction)
        self.formatbar.addAction(strikeAction)
        self.formatbar.addAction(superAction)
        self.formatbar.addAction(subAction)

        self.formatbar.addSeparator()

        self.formatbar.addAction(alignLeft)
        self.formatbar.addAction(alignCenter)
        self.formatbar.addAction(alignRight)
        self.formatbar.addAction(alignJustify)

        self.formatbar.addSeparator()

        self.formatbar.addAction(indentAction)
        self.formatbar.addAction(dedentAction)

    def initMenubar(self):

        menubar = self.menuBar()

        file = menubar.addMenu("File")
        edit = menubar.addMenu("Edit")
        view = menubar.addMenu("View")

        # Add the most important actions to the menubar

        file.addAction(self.newAction)
        file.addAction(self.openAction)
        file.addAction(self.saveAction)
        file.addAction(self.saveasAction)
        file.addAction(self.exportAction)
        file.addAction(self.printAction)
        file.addAction(self.previewAction)

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.copyAction)
        edit.addAction(self.pasteAction)
        edit.addAction(self.findAction)
        edit.addAction(self.addUrlAction)

        # Toggling actions for the various bars
        toolbarAction = QtWidgets.QAction("Toggle Toolbar", self)
        toolbarAction.triggered.connect(self.toggleToolbar)

        # formatbarAction = QtWidgets.QAction("Toggle Formatbar",self)
        # formatbarAction.triggered.connect(self.toggleFormatbar)

        statusbarAction = QtWidgets.QAction("Toggle Statusbar", self)
        statusbarAction.triggered.connect(self.toggleStatusbar)

        view.addAction(toolbarAction)
        # view.addAction(formatbarAction)
        view.addAction(statusbarAction)

    def initUI(self):

        self.text = MyPlainTextEdit(self)

        # Set the tab stop width to around 33 pixels which is
        # more or less 8 spaces
        self.text.setTabStopWidth(33)

        self.initToolbar()
        # Formatbar removed from gig guide
        # self.initFormatbar()
        self.initMenubar()

        self.setCentralWidget(self.text)

        # Initialize a statusbar for the window
        self.statusbar = self.statusBar()

        # If the cursor position changes, call the function that displays
        # the line and column number
        self.text.cursorPositionChanged.connect(self.cursorPosition)

        # We need our own context menu for tables
        # self.text.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.text.customContextMenuRequested.connect(self.context)

        self.text.textChanged.connect(self.changed)
        self.previewTextBrowser = MyDialog(self)
        self.text.completer = None
        self.myHighlighter = highlighter.Highlighter(self.completer, self.text.document(), )
        self.setGeometry(100, 100, 1030, 800)
        self.setWindowTitle(SYSTEMNAME)
        self.setWindowIcon(QtGui.QIcon("icons/icon.png"))
        self.setFocus()

    def changed(self):
        self.changesSaved = False
        return False

    def saveDiscardCancel(self, discardmsg=None):

        popup = QtWidgets.QMessageBox(self)
        popup.setIcon(QtWidgets.QMessageBox.Warning)
        popup.setWindowTitle(SYSTEMNAME)
        popup.setText("The document has been modified")
        popup.setInformativeText("Do you want to save your changes?")
        popup.setStandardButtons(QtWidgets.QMessageBox.Save |
                                 QtWidgets.QMessageBox.Cancel |
                                 QtWidgets.QMessageBox.Discard)
        popup.setDefaultButton(QtWidgets.QMessageBox.Save)
        answer = popup.exec_()

        if answer == QtWidgets.QMessageBox.Save:
            return SAVE
        elif answer == QtWidgets.QMessageBox.Discard:
            return DISCARD
        else:
            return CANCEL

    def closeEvent(self, event):

        if self.changesSaved or len(self.text.toPlainText()) == 0:
            event.accept()
        else:
            answer = self.saveDiscardCancel()
            if answer == SAVE:
                self.save()
                event.accept
            elif answer == DISCARD:
                event.accept()
            else:  # CANCEL
                event.ignore()

    def context(self, pos):
        # debug - tentatively eliminating - probably not required
        return False

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table, if there is one
        table = cursor.currentTable()

        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:

            menu = QtGui.QMenu(self)

            appendRowAction = QtWidgets.QAction("Append row", self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))

            appendColAction = QtWidgets.QAction("Append column", self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))

            removeRowAction = QtWidgets.QAction("Remove row", self)
            removeRowAction.triggered.connect(self.removeRow)

            removeColAction = QtWidgets.QAction("Remove column", self)
            removeColAction.triggered.connect(self.removeCol)

            insertRowAction = QtWidgets.QAction("Insert row", self)
            insertRowAction.triggered.connect(self.insertRow)

            insertColAction = QtWidgets.QAction("Insert column", self)
            insertColAction.triggered.connect(self.insertCol)

            mergeAction = QtWidgets.QAction("Merge cells", self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))

            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)

            splitAction = QtWidgets.QAction("Split cells", self)

            cell = table.cellAt(cursor)

            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:

                splitAction.triggered.connect(lambda: table.splitCell(cell.row(), cell.column(), 1, 1))

            else:
                splitAction.setEnabled(False)

            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)

            menu.addSeparator()

            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)

            menu.addSeparator()

            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)

            menu.addSeparator()

            menu.addAction(mergeAction)
            menu.addAction(splitAction)

            # Convert the widget coordinates into global coordinates
            pos = self.mapToGlobal(pos)

            # Add pixels for the tool and formatbars, which are not included
            # in mapToGlobal(), but only if the two are currently visible and
            # not toggled by the user

            if self.toolbar.isVisible():
                pos.setY(pos.y() + 45)

            if self.formatbar.isVisible():
                pos.setY(pos.y() + 45)

            # Move the menu to the new position
            menu.move(pos)

            menu.show()

        else:

            event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse, QtCore.QPoint())

            self.text.contextMenuEvent(event)

    # never called
    def removeRow(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's row
        table.removeRows(cell.row(), 1)

    # never called
    def removeCol(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's column
        table.removeColumns(cell.column(), 1)

    # never called
    def insertRow(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertRows(cell.row(), 1)

    # never called
    def insertCol(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertColumns(cell.column(), 1)


    def toggleToolbar(self):

        state = self.toolbar.isVisible()

        # Set the visibility to its inverse
        self.toolbar.setVisible(not state)

    # never called
    def toggleFormatbar(self):

        state = self.formatbar.isVisible()

        # Set the visibility to its inverse
        self.formatbar.setVisible(not state)

    def toggleStatusbar(self):

        state = self.statusbar.isVisible()

        # Set the visibility to its inverse
        self.statusbar.setVisible(not state)

    def new(self):

        if self.changesSaved or len(self.text.toPlainText()) == 0:
            pass
        else:
            answer = self.saveDiscardCancel()
            if answer == SAVE:
                self.save()
            elif answer == DISCARD:
                pass
            else:  # CANCEL
                return

        self.text.clear()
        dt = datetime.today()
        nextWednesday = dt + timedelta(days=(9 - dt.weekday()))
        for i in range(0, 7):
            idate = nextWednesday + timedelta(days=i)
            self.text.insertPlainText(idate.strftime("%A %d %B\n"))
            self.text.insertPlainText("[                      {                         :                     \n")
            self.text.insertPlainText("[                      {                         :                     \n")
            self.text.insertPlainText("[                      {                         :                     \n")
            self.text.insertPlainText("[                      {                         :                     \n")
            self.text.insertPlainText("[                      {                         :                     \n")
            self.text.insertPlainText("[                      {                         :                     \n")


            # avoid pesky carriage return at end of document
            if i < 6:
                self.text.insertPlainText("\n")
        self.changesSaved = False

    def open(self):
        if self.changesSaved or len(self.text.toPlainText()) == 0:
            pass
        else:
            answer = self.saveDiscardCancel()
            if answer == SAVE:
                self.save()
            elif answer == DISCARD:
                pass
            else:  # CANCEL
                return
        # Get filename and show only .writer files
        # PYQT5 Returns a tuple in PyQt5, we only need the filename
        self.filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', ".", "(*.txt)")[0]

        if self.filename:
            with open(self.filename, "rt") as file:
                self.text.setPlainText(file.read())

    def save(self):

        # Only open dialog if there is no filename yet
        # PYQT5 Returns a tuple in PyQt5, we only need the filename
        if not self.filename:
            self.filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')[0]

        if self.filename:

            # Append extension if not there yet
            if not self.filename.endswith(".txt"):
                self.filename += ".txt"

            # We just store the contents of the text file
            # option to add html conversion later
            with open(self.filename, "wt") as file:
                # file.write(self.text.toHtml())
                file.write(self.text.toPlainText())

            self.changesSaved = True

    def saveas(self):

        # Always open dialog irrespective of whether there is a filename yet
        # PYQT5 Returns a tuple in PyQt5, we only need the filename
        self.filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')[0]

        if self.filename:

            # Append extension if not there yet
            if not self.filename.endswith(".txt"):
                self.filename += ".txt"

            # We just store the contents of the text file
            with open(self.filename, "wt") as file:
                # file.write(self.text.toHtml())
                file.write(self.text.toPlainText())

            self.changesSaved = True

    def export(self):
        # self.generateHTML()
        self.generateRTF()

        print(self.exportfinal)
        # Always open dialog irrespective of whether there is a filename yet
        # PYQT5 Returns a tuple in PyQt5, we only need the filename

        exportfilename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                               'Save Exported html File', DEFAULTDIRECTORY, "*.rtf")[0]

        if exportfilename:
            # exportFilename1 = path.dirname(exportfilename) + "/" +  path.basename(exportfilename) +".htm"
            # We just store the contents of the text file
            with open(exportfilename, "wt") as file:
                # file.write(self.text.toHtml())
                file.write(self.exportfinal)

    def preview(self):
        self.generateHTML()
        self.previewTextBrowser.textBrowser.setHtml(self.exportfinal)
        self.previewTextBrowser.show()

        print("BROWSED " + self.exportfinal)
        # Open preview dialog
        # preview = QtPrintSupport.QPrintPreviewDialog()

        # If a print is requested, open print dialog
        # preview.paintRequested.connect(lambda p: self.text.print_(p))

        # preview.exec_()

    def generateHTML(self):

        codetop = ('<!DOCTYPE html> <html lang="en"> <head> <meta charset="utf-8"> '
                   '<title>Brisbane Live Music Guide</title> </head> <body>')
        codetail = '</body></html>'

        linktop = ' <a href="'
        linkmid = '">'
        linktail = '</a> '
        linkfb = linktop + 'http\\1' + linkmid + 'FB' + linktail
        linkv = linktop + 'http\\1' + linkmid + 'V' + linktail

        newline = '<br > \n'

        self.bandrules = copy.deepcopy(self.completer.bigdictionary["bandnamelist"])
        self.venuerules = copy.deepcopy(self.completer.bigdictionary["venuenamelist"])
        exportstring = self.text.toPlainText()
        exportstring = re.sub('\t', ' ', exportstring)
        exportstring = re.sub('\[*\{*', '', exportstring)
        exportstring = re.sub(r'http(\S+facebook\.com\S+)\s', r'xxxxtp\1 ', exportstring)
        exportstring = re.sub(r'http(\S+)\s', r'yyyytp\1 ', exportstring)
        exportstring = exportstring + " "  # ugly but avoids problem with lack of white space at end of file
        exportstring = re.sub(r'xxxxtp(\S+)\s', linkfb, exportstring)
        exportstring = re.sub(r'yyyytp(\S+)\s', linkv, exportstring)

        for key, value in self.bandrules.items():
            try:
                bandname = re.compile(key)
            except:
                print("Whoops compile bandname key failed" + key)
            subline = linktop + value + linkmid + key + linktail

            exportstring = re.sub(bandname, subline, exportstring)
        for key, value in self.venuerules.items():
            try:
                venuename = re.compile(key)
            except:
                print(key)
            subline = linktop + value + linkmid + key + linktail

            exportstring = re.sub(venuename, subline, exportstring)
        exportstring = re.sub('\n(\s*)', newline, exportstring)
        exportstring = re.sub(' +', " ", exportstring)
        exportstring = re.sub(' :', ':', exportstring)
        exportstring = re.sub('\n: <br >', '', exportstring)

        self.exportfinal = codetop + exportstring + codetail

    def generateRTF(self):

        # need to handle special chars (some single quotes?)
        # double quotes - 2 directions,
        # backslashes and
        # hyphen

        codetop = ("{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033\n"
                   "{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}\n"
                   "{\\colortbl;\\red0\\green0\\blue0;\\red255\\green0\\blue0;\\red0\\green0\\blue255;}\n"
                   "{\\f0\\fs22\\cf1")
        codetail = '}}'

        linktop = '}{\\field{\\*\\fldinst {HYPERLINK "'
        linkmid = '" }}{\\fldrslt {\\ul\\cf3'
        linktail = '}}}{\\f0\\fs22\\cf1{ }'
        linkfb = repr(linktop) + 'http\\1' + repr(linkmid) + 'FB' + repr(linktail)
        linkfb = linkfb.translate(str.maketrans({"'": None}))
        linkv = repr(linktop) + 'http\\1' + repr(linkmid) + 'V' + repr(linktail)
        linkv = linkv.translate(str.maketrans({"'": None}))

        newline = '\\line \n'

        self.bandrules = copy.deepcopy(self.completer.bigdictionary["bandnamelist"])
        self.venuerules = copy.deepcopy(self.completer.bigdictionary["venuenamelist"])
        exportstring = self.text.toPlainText()
        exportstring = re.sub('\t', ' ', exportstring)
        exportstring = re.sub('\[*\]*\{*\}*<*>*', '', exportstring)
        exportstring = re.sub(r'http(\S+facebook\.com\S+)\s', r'xxxxtp\1 ', exportstring)
        exportstring = exportstring + " "  # ugly but avoids problem with lack of white space at end of file
        exportstring = re.sub(r'http(\S+)\s', r'yyyytp\1', exportstring)
        exportstring = exportstring + " "  # ugly but avoids problem with lack of white space at end of file
        exportstring = re.sub(r'xxxxtp(\S+)\s', linkfb, exportstring)
        exportstring = exportstring + " "  # ugly but avoids problem with lack of white space at end of file
        exportstring = re.sub(r'yyyytp(\S+)\s', linkv, exportstring)

        for key, value in self.bandrules.items():
            try:
                bandname = re.compile(key)
            except:
                print("Whoops compile bandname key failed" + key)
            subline = repr(linktop + value + linkmid + key + linktail).translate(str.maketrans({"'": None}))

            exportstring = re.sub(bandname, subline, exportstring)
        for key, value in self.venuerules.items():
            try:
                venuename = re.compile(key)
            except:
                print(key)
            subline = repr(linktop + value + linkmid + key + linktail).translate(str.maketrans({"'": None}))

            exportstring = re.sub(venuename, subline, exportstring)
        # replace all python newline chars with newline expressed in target language
        exportstring = re.sub('\n(\s*)', newline, exportstring)
        # compress all multiple spaces to single space
        exportstring = re.sub(' +', " ", exportstring)
        exportstring = re.sub('{ } ', '{ }', exportstring)
        # replace unicode apostrophes with ascii single quotes - not good in Open Office
        exportstring = re.sub(chr(8217), "'", exportstring)
        exportstring = re.sub('\n: \\\\line ', '', exportstring)
        self.exportfinal = codetop + exportstring + codetail


    def printHandler(self):

        # Open printing dialog
        dialog = QtPrintSupport.QPrintDialog()

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.text.document().print_(dialog.printer())

    def cursorPosition(self):

        cursor = self.text.textCursor()

        # Mortals like 1-indexed things
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()
        if self.changesSaved:
            cs = ""
        else:
            cs = "<unsaved changes>"
        # print(str(line) + " " + str(col) + " " + str(self.text.textCursor()))
        self.statusbar.showMessage("Line: {} | Column: {}  {}  {}".format(line, col, cs, self.statusbarmsg))
        self.statusbarmsg = ""
        return False

    def addUrl(self):
        thisdocument = self.text.toPlainText()
        thiscursor = self.text.textCursor()
        selectionstart = thiscursor.selectionStart()
        thisselection = thisdocument[selectionstart: thiscursor.selectionEnd()]
        thisselection = re.sub(',','_',thisselection)
        thisselection = re.sub('\n',' ',thisselection)

        poke = selectionstart - 1
        foundplace = False
        while not foundplace:
            if poke == -1:
                self.completer.currentfiletype = ""
                foundplace = True
            elif thisdocument[poke] in ["/n", ':']:
                self.completer.currentfiletype = ""
                foundplace = True
            elif thisdocument[poke] == "{":
                self.completer.currentfiletype = "venuenamelist"
                foundplace = True
            elif thisdocument[poke] == "[":
                self.completer.currentfiletype = "bandnamelist"
                foundplace = True
            poke = poke - 1

        if not self.completer.currentfiletype:
            QtWidgets.QMessageBox.information(None, 'Hint', "Hmmm, can't add a url here!" )
        else:
            thisurl, ok = QtWidgets.QInputDialog.getText(self, "Type url for this band", thisselection , QtWidgets.QLineEdit.Normal, "http://")

            if ok:
                thisurl = re.sub(',', '_', thisurl)
                thisurl = re.sub('\n', ' ', thisurl)
                dt = datetime.now()
                timestamp = dt.strftime("%Y%m%d%H%M%S")
                currentfilepath = PREFERENCES[self.completer.currentfiletype]
                backupfilepath = currentfilepath[:-4] + timestamp + '.txt'
                print(currentfilepath)
                print(backupfilepath)
                #find pathname for band dictionary
                try:
                    shutil.copyfile(currentfilepath, backupfilepath)
                except IOError:
                    QtWidgets.QMessageBox.information(None, 'Whoops', "Hmmm, adding url failed - file backup didn't work")
                else:
                    try:
                        with open(currentfilepath, "a") as dictfile:
                            dictfile.write('\n' + thisselection + ',' + thisurl)
                        self.completer.bigdictionary[self.completer.currentfiletype][thisselection] = thisurl
                        self.completer.words[self.completer.currentfiletype].append(thisselection)
                        self.completer.changeModel(self.completer.currentfiletype)
                        self.myHighlighter.addHighlightRule(thisselection,self.completer.currentfiletype)

                    except IOError:
                        QtWidgets.QMessageBox.information(None, 'Whoops', "Hmmm, adding url failed - file append didn't work")








    def wordCount(self):

        wc = wordcount.WordCount(self)

        wc.getText()

        wc.show()

    # never called
    def insertImage(self):

        # Get image file name
        # PYQT5 Returns a tuple in PyQt5
        filename = \
        QtWidgets.QFileDialog.getOpenFileName(self, 'Insert image', ".", "Images (*.png *.xpm *.jpg *.bmp *.gif)")[0]

        if filename:

            # Create image object
            image = QtGui.QImage(filename)

            # Error if unloadable
            if image.isNull():

                popup = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                              "Image load error",
                                              "Could not load image file!",
                                              QtWidgets.QMessageBox.Ok,
                                              self)
                popup.show()

            else:

                cursor = self.text.textCursor()

                cursor.insertImage(image, filename)

    # never called
    def fontColorChanged(self):

        # Get a color from the text dialog
        color = QtWidgets.QColorDialog.getColor()

        # Set it as the new text color
        self.text.setTextColor(color)

    # never called
    def highlight(self):

        color = QtWidgets.QColorDialog.getColor()

        self.text.setTextBackgroundColor(color)

    # never called
    def bold(self):

        if self.text.fontWeight() == QtGui.QFont.Bold:

            self.text.setFontWeight(QtGui.QFont.Normal)

        else:

            self.text.setFontWeight(QtGui.QFont.Bold)

    # never called
    def italic(self):

        state = self.text.fontItalic()

        self.text.setFontItalic(not state)

    # never called
    def underline(self):

        state = self.text.fontUnderline()

        self.text.setFontUnderline(not state)

    # never called
    def strike(self):

        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # And set the next char format
        self.text.setCurrentCharFormat(fmt)

    # never called
    def superScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)

        else:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    # never called
    def subScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)

        else:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)  # extra = (len(completion) -
        #         len(self.completer.completionPrefix()))
        # hmmm why was this here?
        # tc.movePosition(QtGui.QTextCursor.Left)
        # tc.movePosition(QtGui.QTextCursor.EndOfWord)
        # tc.insertText(completion[-extra:])

    # never called
    def alignLeft(self):
        self.text.setAlignment(Qt.AlignLeft)

    # never called
    def alignRight(self):
        self.text.setAlignment(Qt.AlignRight)

    # never called
    def alignCenter(self):
        self.text.setAlignment(Qt.AlignCenter)

    # never called
    def alignJustify(self):
        self.text.setAlignment(Qt.AlignJustify)

    # never called
    def indent(self):
        # Grab the cursor
        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's end
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QtGui.QTextCursor.Up if diff > 0 else QtGui.QTextCursor.Down

            # Iterate over lines (diff absolute value)
            for n in range(abs(diff) + 1):
                # Move to start of each line
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)

                # Insert tabbing
                cursor.insertText("\t")

                # And move back up
                cursor.movePosition(direction)

        # If there is no selection, just insert a tab
        else:

            cursor.insertText("\t")

    # never called
    def handleDedent(self, cursor):

        cursor.movePosition(QtGui.QTextCursor.StartOfLine)

        # Grab the current line
        line = cursor.block().text()

        # If the line starts with a tab character, delete it
        if line.startswith("\t"):

            # Delete next character
            cursor.deleteChar()

        # Otherwise, delete all spaces until a non-space character is met
        else:
            for char in line[:8]:

                if char != " ":
                    break

                cursor.deleteChar()

    # never called
    def dedent(self):

        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's last line
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QtGui.QTextCursor.Up if diff > 0 else QtGui.QTextCursor.Down

            # Iterate over lines
            for n in range(abs(diff) + 1):
                self.handleDedent(cursor)

                # Move up
                cursor.movePosition(direction)

        else:
            self.handleDedent(cursor)

    # never called
    def bulletList(self):

        cursor = self.text.textCursor()

        # Insert bulleted list
        cursor.insertList(QtGui.QTextListFormat.ListDisc)

    # never called
    def numberList(self):

        cursor = self.text.textCursor()

        # Insert list with numbers
        cursor.insertList(QtGui.QTextListFormat.ListDecimal)

    def band(self):
        self.setCompleter()

    def venue(self):
        completer = self.text.completer
        self.setCompleter()

    def setCompleter(self, completer):
        print("setCompleter invoked")
        # method binds completer to QPlainTextEdit widget
        if self.completer.currentfiletype:
            if self.text.completer:
                self.text.disconnect(self.text.completer, 0, self.text, 0)
            if not completer:
                return

            # setWidget transfers ownership of specified widget to Qt
            # #- automatic for QLineEdit or QComboBox but not for QPlainTextEdit
            completer.setWidget(self.text)
            # CompletionMode can be PopupCompletion, InlineCompletion or UnfilteredPopupCompletion
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.text.completer = completer
            self.text.completer.activated.connect(self.text.insertCompletion)


def main():
    app = QtWidgets.QApplication(sys.argv)
    autocompleter = DictionaryCompleter()
    main = Main(autocompleter)
    main.setCompleter(autocompleter)
    main.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()