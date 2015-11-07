from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time


class Form(QDialog):
    """ Just a simple dialog with a couple of widgets
    """
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.browser = QTextBrowser()
        self.setWindowTitle('Just a dialog')
        self.lineedit = QLineEdit("Write something and press Enter")
        self.lineedit.selectAll()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        layout.addWidget(self.lineedit)
        self.setLayout(layout)
        self.lineedit.setFocus()
        self.connect(self.lineedit, SIGNAL("returnPressed()"),
                     self.update_ui)

    def update_ui(self):
        self.browser.append(self.lineedit.text())


if __name__ == "__main__":
    import sys, time

    app = QApplication(sys.argv)

    # Create and display the splash screen
    splash_pix = QPixmap(r'./splash2.png')

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    # adding progress bar
    progressBar = QProgressBar(splash)



    splash.setMask(splash_pix.mask())


    splash.show()
    for i in range(0, 100):
        progressBar.setValue(i)
        t = time.time()
        while time.time() < t + 0.1:
           app.processEvents()



    # Simulate something that takes time
    time.sleep(2)

    form = Form()
    form.show()
    splash.finish(form)
    app.exec_()