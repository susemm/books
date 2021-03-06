#!/usr/bin/python
# coding=utf8

__author__ = 'vin@misday.com'

import os, sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from main_ui import *
from downloader_ui import *
from pyvin import ux
from duoSpider import Special
from duoMain import Duokan, Downloader, Config

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

def _fromQString(s):
    try:
        return str(s.toLocal8Bit())
    except:
        return s

class MainWindow(QMainWindow):
    tsize = (20, 20)

    BG_FREED = QtGui.QColor(255, 255, 153)
    BG_DOWN = QtGui.QColor(146, 208, 80)

    (COLUMN_ID, COLUMN_TITLE, COLUMN_AUTHOR, COLUMN_LINK, COLUMN_PROGRESS) = range(0, 5)
    COLUMNS_WIDTH = [50, 200, 200, 200, 200, 100]

    def __init__(self):
        self.duokan     = Duokan()
        self.conf       = Config()
        self.special    = None
        self.downloader = None
        self.powerOff   = False

        self.tag = MainWindow.__name__
        super( MainWindow, self ).__init__()

        self.ui= Ui_MainWindow()
        self.ui.setupUi(self)
        self.setupPopup()

        self.bindSignal()

    def setupPopup(self):
        self.ui.tableWidget_books.addAction(self.ui.action_list_view_in_browser)
        self.ui.tableWidget_books.addAction(self.ui.action_list_download)
        self.ui.tableWidget_books.addAction(self.ui.action_list_remove)
        self.ui.tableWidget_books.addAction(self.ui.action_list_merge)
        self.ui.tableWidget_books.addAction(self.ui.action_list_crop)
        self.ui.tableWidget_books.addAction(self.ui.action_list_rename)
        self.ui.tableWidget_books.addAction(self.ui.action_list_mark_download)

    def bindSignal(self):
        QtCore.QObject.connect(self, QtCore.SIGNAL("when_information(QString, QString)"), self.do_message)
        QtCore.QObject.connect(self, QtCore.SIGNAL("when_item_progress(QString, QString)"), self.do_itemProgress)
        QtCore.QObject.connect(self, QtCore.SIGNAL("when_add_book(QString, QString, QString, QString, bool, bool)"), self.appendItem)

    def appendItem(self, id, title='', author='', link='', freed=False, done=False):
        row = self.ui.tableWidget_books.rowCount()
        self.when_add_book(row)

        item = QTableWidgetItem(id)
        self.ui.tableWidget_books.setItem(row, MainWindow.COLUMN_ID, item)

        item = QTableWidgetItem(title)
        self.ui.tableWidget_books.setItem(row, MainWindow.COLUMN_TITLE, item)

        item = QTableWidgetItem(author)
        self.ui.tableWidget_books.setItem(row, MainWindow.COLUMN_AUTHOR, item)

        item = QTableWidgetItem(link)
        self.ui.tableWidget_books.setItem(row, MainWindow.COLUMN_LINK, item)

        # item = QTableWidgetItem(progress)
        item = QProgressBar(self)
        item.setRange(0, 100)
        item.setValue(0)
        item.setTextVisible(True)
        item.setMaximumHeight(15)
        item.setTextDirection(QtGui.QProgressBar.TopToBottom)
        self.ui.tableWidget_books.setCellWidget(row, MainWindow.COLUMN_PROGRESS, item)

        if freed:
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).setBackgroundColor(MainWindow.BG_FREED)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).setBackgroundColor(MainWindow.BG_FREED)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_AUTHOR).setBackgroundColor(MainWindow.BG_FREED)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_LINK).setBackgroundColor(MainWindow.BG_FREED)
        if done:
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).setBackgroundColor(MainWindow.BG_DOWN)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).setBackgroundColor(MainWindow.BG_DOWN)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_AUTHOR).setBackgroundColor(MainWindow.BG_DOWN)
            self.ui.tableWidget_books.item(row, MainWindow.COLUMN_LINK).setBackgroundColor(MainWindow.BG_DOWN)

        self.adjustListWidth()

    def adjustListWidth(self):
        self.ui.tableWidget_books.resizeColumnsToContents()

    # set download column progress
    def setProgress(self, row, prog):
        if row >= 0 and row < self.ui.tableWidget_books.rowCount():
            item = self.ui.tableWidget_books.cellWidget(row, MainWindow.COLUMN_PROGRESS)
            item.setValue(prog)

    # for duoSpider
    def cbAddUrl(self, event, url):
        self.when_special_url(url)

    # for duoSpider
    def cbAddBook(self, event, id, title, author, link):
        notFreed = self.duokan.addBook(id, title, author, link)
        download = self.duokan.isDownload(id)
        self.when_add_book_info(id, title, author, link, (not notFreed), download)

    def startDownload(self):
        if self.downloadRow < self.ui.tableWidget_books.rowCount():
            id = _fromQString(self.ui.tableWidget_books.item(self.downloadRow, MainWindow.COLUMN_ID).text())
            proxy = self.conf.getProxy()
            self.downloader = Downloader(id, id, proxy[0], proxy[1], proxy[2])
            self.downloader.bind(Downloader.EVT_START, self.cbStart)
            self.downloader.bind(Downloader.EVT_STOP, self.cbStop)
            self.downloader.bind(Downloader.EVT_LOG, self.cbLog)
            self.downloader.bind(Downloader.EVT_PROG, self.cbProgress)
            self.downloader.start()

    # for downloader
    def cbStart(self, event):
        self.when_itemProgress(self.downloadRow, 100)
        self.when_progress(0)

    # for downloader
    def cbStop(self, event):
        self.when_itemProgress(self.downloadRow, 100)
        self.when_progress(100)
        # self.list.SetItemBackgroundColour(self.downloadIdx, MainWindow.BG_DOWN)

        # start next
        self.downloadRow += 1
        self.startDownload()

        if self.downloadRow >= self.ui.tableWidget_books.rowCount():
            if self.powerOff:
                os.system('shutdown -t 60 -f -s')

    # for downloader
    def cbLog(self, event, str):
        self.when_logging(str)

    # for downloader
    def cbProgress(self, event, prog):
        self.when_progress(prog)

### signals and slots
    # signals
    def when_logging(self, logStr):
        self.emit(QtCore.SIGNAL("when_logging(QString)"), logStr)

    def when_special_url(self, url):
        self.emit(QtCore.SIGNAL("when_special_url(QString)"), url)

    def when_status(self, text):
        self.emit(QtCore.SIGNAL("when_status(QString)"), text)
    def when_add_book(self, row):
        self.emit(QtCore.SIGNAL("when_add_book(int)"), row)

    def when_del_book(self, row):
        self.emit(QtCore.SIGNAL("when_del_book(int)"), row)

    def when_progress(self, prog):
        self.emit(QtCore.SIGNAL("when_progress(int)"), prog)

    # self defined signal##############################################################################################
    def when_information(self, text, title='', info=True):
        self.emit(QtCore.SIGNAL("when_status(QString)"), '%s --> %s' % (title, text))
        if info:
            self.emit(QtCore.SIGNAL("when_information(QString, QString)"), text, title)

    def when_itemProgress(self, row, prog):
        self.emit(QtCore.SIGNAL("when_item_progress(int, int)"), row, prog)

    def when_add_book_info(self, id, title, author, link, freed=False, done=False):
        self.emit(QtCore.SIGNAL("when_add_book(QString, QString, QString, QString, bool, bool)"),
                  _fromUtf8(id), _fromUtf8(title), _fromUtf8(author), _fromUtf8(link), freed, done)

    # slots
    def do_update(self):
        self.when_progress(10)
        proxy = self.conf.getProxy()
        self.special = Special(proxy[0], proxy[1], proxy[2])
        self.special.bind(Special.EVT_FIND_LINK, self.cbAddUrl)
        self.special.bind(Special.EVT_FIND_BOOK, self.cbAddBook)
        self.special.start()
        self.when_progress(100)

    def do_update_stop(self):
        if self.special:
            self.special.stop()
            self.special = None

    def do_download_all(self):
        self.dlgs = []
        for row in range(self.ui.tableWidget_books.rowCount()):
            id    = self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text()
            title = self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).text()
            dlg = DownloaderDlg(self, self.conf, title)
            dlg.setId(id)
            dlg.setName(id)
            dlg.show()
            dlg.resize(640, 200)
            self.dlgs.append(dlg)

        if self.dlgs:
            for i, dlg in enumerate(self.dlgs):
                if i < 5:
                    x = 0
                    y = 190 * i
                else:
                    x = 640
                    y = 190 * (i - 5)
                dlg.resize(640, 190)
                dlg.move(x, y)

    def do_download_stop(self):
        pass

    def do_open_special_in_browser(self):
        self.duokan.openInNewTab(_fromQString(self.ui.lineEdit_specialUrl.text()))

    def do_open_books_folder(self):
        '''open books/new folder'''
        self.duokan.openNewFolder()

    def do_clean_tmp_folder(self):
        self.duokan.cleanTmp()
        self.when_information( 'Finished', 'Clear tmp folder')

    def do_merge_all(self):
        for row in range(self.ui.tableWidget_books.rowCount()):
            id = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            self.duokan.merge(id)
        self.when_information('merge all finished')

    def do_crop_all(self):
        for row in range(self.ui.tableWidget_books.rowCount()):
            id = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            self.duokan.crop(id)
        self.when_information('crop all finished')

    def do_rename_all(self):
        self.duokan.renameAll()
        self.when_information('Finished', 'Rename All')

    def do_done_all(self):
        for row in range(self.ui.tableWidget_books.rowCount()):
            id    = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            title = self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).text()
            self.when_information('Start', 'Merge & Crop & Rename [%s]' % title, False)
            self.duokan.setDownload(id)
            self.duokan.merge(id)
            self.duokan.crop(id)
            self.duokan.rename(id)
            self.when_information('Finished!', 'Merge & Crop & Rename [%s]' % title, False)
        self.when_information('Finished!', 'All Merge & Crop & Rename')

    def do_crop_book(self):
        file_wildcard = "Pdf files (*.pdf)"
        filePath = QFileDialog.getOpenFileName(self, 'Open file to crop', _fromUtf8(os.path.join(os.getcwd(), 'books')), _fromUtf8(file_wildcard))
        if filePath:
            self.duokan.cropSingle(_fromQString(filePath))
            self.when_information( 'Finished!', 'Crop single')

    def do_merge_book(self):
        filePath = QFileDialog.getExistingDirectory(self, 'Open file to crop', _fromUtf8(os.path.join(os.getcwd(), 'tmp')))
        if filePath:
            print _fromQString(filePath)
            self.duokan.mergeSingle(_fromQString(filePath))
            self.when_information('Finished!', 'Merge single')

    def do_crop_4print(self):
        file_wildcard = "Pdf files (*.pdf)"
        filePath = QFileDialog.getOpenFileName(self, 'Open file to crop for printing', _fromUtf8(os.path.join(os.getcwd(), 'books')), _fromUtf8(file_wildcard))
        if filePath:
            self.duokan.crop4Print(_fromQString(filePath))
            self.when_information( 'Finished!', 'Crop for printing')

    def do_crop_4kindle(self):
        file_wildcard = "Pdf files (*.pdf)"
        filePath = QFileDialog.getOpenFileName(self, 'Open file to crop for printing', _fromUtf8(os.path.join(os.getcwd(), 'books')), _fromUtf8(file_wildcard))
        if filePath:
            self.duokan.crop4Kindle(_fromQString(filePath))
            self.when_information( 'Finished!', 'Crop for kindle')

    def do_crop_4nook(self):
        file_wildcard = "Pdf files (*.pdf)"
        filePath = QFileDialog.getOpenFileName(self, 'Open file to crop for printing', _fromUtf8(os.path.join(os.getcwd(), 'books')), _fromUtf8(file_wildcard))
        if filePath:
            self.duokan.crop4Nook(_fromQString(filePath))
            self.when_information('Finished!', 'Crop for nook')

    def on_power_off_setting(self, powerOff):
        self.powerOff = powerOff
        # print powerOff

    def do_destroyed(self):
        print 'destroyed'

    def do_list_view_in_browser(self):
        ''' open link in browser '''
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            url = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_LINK).text())
            self.duokan.openInNewTab(url)

    def do_list_download(self):
        '''download a book'''
        row = self.ui.tableWidget_books.currentRow()
        if row >=0 and row < self.ui.tableWidget_books.rowCount():
            id    = self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text()
            title = self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).text()
            dlg = DownloaderDlg(self, self.conf, title)
            dlg.setId(id)
            dlg.setName(id)
            dlg.show()
        else:
            dlg = DownloaderDlg(self, self.conf)
            dlg.show()

    def do_list_remove(self):
        ''' delete an item '''
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            self.when_del_book(row)

    def do_list_merge(self):
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            id = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            self.duokan.merge(id)
            self.when_information('merge finished')

    def do_list_crop(self):
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            id = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            self.duokan.crop(id)
            self.when_information('crop finished')

    def do_list_rename(self):
        ''' rename a item from id to title '''
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            id    = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            title = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_TITLE).text())
            self.duokan.rename(id, title)
            self.when_information('rename finished')

    def do_list_mark_download(self, row, col):
        row = self.ui.tableWidget_books.currentRow()
        if row != -1:
            id = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_ID).text())
            self.duokan.setDownload(id)

    def do_list_dclick(self, row, col):
        url = _fromQString(self.ui.tableWidget_books.item(row, MainWindow.COLUMN_LINK).text())
        self.duokan.openInNewTab(url)

    # self defined slots ###############################################################################################
    def do_message(self, text, title=''):
        QtGui.QMessageBox.information(self, title, text)

    def do_itemProgress(self, row, prog):
        self.setProgress(row, prog)

class DownloaderDlg(QDialog):
    def __init__(self, parent=None, conf=None, tt=''):
        super(DownloaderDlg, self).__init__(parent)

        self.conf = conf
        self.downloader = None

        self.ui= Ui_Dialog()
        self.ui.setupUi(self)
        self.when_title(tt)

    def start(self):
        # title = _fromQString(self.windowTitle())
        bid   = _fromQString(self.ui.lineEdit_id.text())
        name  = _fromQString(self.ui.lineEdit_name.text())

        self.when_message('Title: %s' % self.windowTitle().toUtf8())
        self.when_message('ID: %s' % bid)
        self.when_message('Name: %s' % name)
        self.when_message('downloading...')
        self.when_message('---------')

        proxy = self.conf.getProxy()
        self.downloader = Downloader(bid, name, proxy[0], proxy[1], proxy[2])
        self.downloader.bind(Downloader.ON_STOP, self.cbStop)
        self.downloader.bind(Downloader.EVT_LOG, self.cbLog)
        self.downloader.bind(Downloader.EVT_PROG, self.cbProgress)
        self.downloader.start()

    def stop(self):
        if self.downloader:
            self.downloader.stop()
            self.downloader = None

    def cbStop(self, event):
        self.when_progress(100)
        self.downloader = None

    def cbLog(self, event, msgStr):
        self.when_message(msgStr)

    def cbProgress(self, event, prog):
        self.when_progress(prog)

    def setId(self, id):
        self.when_id(id)
    def setName(self, name):
        self.when_name(name)

#### slots & signals ##################################################################################################
    def do_start(self, checked):
        ''' start download process '''
        if checked:
            print 'checked'
            self.start()
        else:
            print 'unchecked'
            self.stop()

    def do_stop(self):
        ''' stop download process '''
        print 'destroy'
        self.stop()

    def when_id(self, id):
        self.emit(QtCore.SIGNAL('when_id(QString)'), id)
    def when_name(self, name):
        self.emit(QtCore.SIGNAL('when_name(QString)'), name)
    def when_progress(self, prog):
        self.emit(QtCore.SIGNAL('when_progress(int)'), prog)
    def when_message(self, msgStr):
        self.emit(QtCore.SIGNAL('when_message(QString)'), _fromUtf8(msgStr))
    def when_title(self, title):
        self.emit(QtCore.SIGNAL('when_title(QString)'), title)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()