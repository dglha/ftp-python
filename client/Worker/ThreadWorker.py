import time
import sys
import traceback

from PyQt5.QtCore import Qt, QThread, QRunnable, pyqtSlot, QObject, pyqtSignal


class ThreadWorker(QRunnable):
    """
    Worker Thread
    """

    @pyqtSlot()
    def run(self):
        """
        Code here
        """
        print("Thread started")
        time.sleep(6)
        print("Thread stop")


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        current data len (Download/upload)

    """

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int, str)


class DownloadWorker(QRunnable):
    """
    Download worker thread
    """

    def __init__(self, file_name, file_size, source_file, destination_file, ftp, *args, **kwargs):
        super(DownloadWorker, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.file_name = file_name
        self.file_size = file_size
        self.source_file = source_file
        self.destination_file = destination_file
        self.ftp = ftp
        # Signal
        self.signals = WorkerSignals()
        self.kwargs["progress_callback"] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            with open(self.destination_file, "wb") as file:
                def callback(data):
                    file.write(data)
                    self.signals.progress.emit(len(data), self.source_file)

                self.ftp.retrbinary("RETR " + self.file_name, callback=callback)

            self.ftp.quit()
        except Exception as e:
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

class UploadWorker(QRunnable):
    """
    Upload worker thread
    """

    def __init__(self, file_name, file_size, source_file, destination_file, ftp, *args, **kwargs):
        super(UploadWorker, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.file_name = file_name
        self.file_size = file_size
        self.source_file = source_file
        self.destination_file = destination_file
        self.ftp = ftp
        # Signal
        self.signals = WorkerSignals()
        self.kwargs["progress_callback"] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            with open(self.source_file, "rb") as file:
                def callback(data):
                    self.signals.progress.emit(len(data), self.source_file)

                self.ftp.storbinary("STOR " + self.file_name, fp=file, callback=callback)

            self.ftp.quit()
        except Exception as e:
            print(e)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()
