#!/usr/bin/env python3

import sys
import json

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QKeySequence

from dictionarytreeview import DictionaryTreeView


class Editor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('editor.ui', self)

        self.tree_view = self.findChild(DictionaryTreeView, 'tree_view')

        # Close window (and application) on Ctrl+Q
        shortcut_close = QtWidgets.QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut_close.activated.connect(self.close)

        # Save and open files
        action_open = self.findChild(QtWidgets.QAction, 'action_open')
        action_save = self.findChild(QtWidgets.QAction, 'action_save')

        action_open.triggered.connect(self.load_tree)
        action_save.triggered.connect(self.save_tree)

    def load_tree(self):
        caption = 'Open File'
        filter = 'JSON files (*.json)'

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(caption=caption,
                                                            filter=filter)
        if filename:
            with open(filename) as f:
                self.tree_view.setData(json.load(f))

    def save_tree(self):
        caption = 'Save File'
        filter = 'JSON files (*.json)'

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(caption=caption,
                                                            filter=filter)
        if filename:
            with open(filename, 'w') as f:
                json.dump(self.tree_view.toDict(), f)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = Editor()
    editor.show()
    sys.exit(app.exec())

