#!/usr/bin/env python3

import sys
import json
from functools import partial

from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QKeySequence

from dictionarytreeview import DictionaryTreeView


class Editor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('editor.ui', self)

        self.map_editor = MapEditor(self)

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


class MapEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('map_editor.ui', self)

        # Close window on Escape
        shortcut_close = QtWidgets.QShortcut(QKeySequence('Escape'), self)
        shortcut_close.activated.connect(self.close)

        self.tile_layout = self.findChild(QtWidgets.QGridLayout, 'gridLayout')

        # Add center tile
        self.add_tile()

    def add_tile(self, button=None):
        # Replace tile button if passed in
        if button:
            tile_row, tile_col = self.get_tile_position(button)
            button.deleteLater()
        else:
            tile_row, tile_col = 0, 0

        if tile_row == 0:
            tile_row = 1
            for row in range(self.tile_layout.rowCount(), -1, -1):
                for col in range(self.tile_layout.columnCount(), -1, -1):
                    item = self.tile_layout.itemAtPosition(row, col)
                    if not item:
                        continue

                    index = self.tile_layout.indexOf(item)
                    self.tile_layout.takeAt(index)
                    self.tile_layout.addItem(item, row+1, col)

        if tile_col == 0:
            tile_col = 1
            for row in range(self.tile_layout.rowCount(), -1, -1):
                for col in range(self.tile_layout.columnCount(), -1, -1):
                    item = self.tile_layout.itemAtPosition(row, col)
                    if not item:
                        continue

                    index = self.tile_layout.indexOf(item)
                    self.tile_layout.takeAt(index)
                    self.tile_layout.addItem(item, row, col+1)

        # Add tile
        label = TileLabel(self)
        self.tile_layout.addWidget(label, tile_row, tile_col)

        # Add buttons around tile, where applicable
        for neighbor_col, neighbor_row in [(-1,-1), (0,-1), (1,-1),
                                           (-1, 0), (0, 0), (1, 0),
                                           (-1, 1), (0, 1), (1, 1)]:
            row = tile_row + neighbor_row
            col = tile_col + neighbor_col

            item = self.tile_layout.itemAtPosition(row, col)
            if not item:
                button = TileButton(self)
                button.clicked.connect(partial(self.add_tile, button))
                self.tile_layout.addWidget(button, row, col)

    def get_tile_position(self, tile):
        index = self.tile_layout.indexOf(tile)
        row, col, *_ = self.tile_layout.getItemPosition(index)

        return row, col


class TileLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setFrameShape(QtWidgets.QFrame.Box)


class TileButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setText('...')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = Editor()
    editor.show()
    sys.exit(app.exec())

