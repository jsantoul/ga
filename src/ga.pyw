# /usr/bin/env python
# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul


from PyQt4.QtGui import QApplication
from widgets.MainWindow import MainWindow

def main():
    import sys
    app = QApplication(sys.argv)
    app.setOrganizationDomain("cas")
    app.setApplicationName("GA")
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
