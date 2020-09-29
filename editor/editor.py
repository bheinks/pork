#!/usr/bin/env python3

import sys
import json
from functools import partial

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QKeySequence

from dictionarytreeview import DictionaryTreeView, DictionaryTreeModel


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
        self.map_editor.show()
        caption = 'Save File'
        filter = 'JSON files (*.json)'

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(caption=caption,
                                                            filter=filter)
        if filename:
            with open(filename, 'w') as f:
                json.dump(self.tree_view.toDict(), f)


class MapDictionaryTreeView(DictionaryTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.map_editor = None

        # Initialize model
        self.model = MapDictionaryTreeModel(['Key', 'Value'])
        self.setModel(self.model)

        # Resize columns to view size
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def build_menu(self, position):
        menu = super().build_menu(position)

        # Only display without item selected
        if not self.indexAt(position).isValid():
            add_map_action = menu.addAction('Add Map')
            add_map_action.triggered.connect(self.add_map)

        return menu

    def add_map(self):
        # Only one map instance
        if 'Map' not in [c.data(0) for c in self.model.rootItem.childItems]:
            # Initialize map editor
            self.map_editor = MapEditor(self)

            # Add key
            item = self.model.rootItem.appendChild(['Map', None])

            # Add button as value
            index = self.model.index(item.childNumber(), 1)
            button = QtWidgets.QPushButton(self)
            button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            button.setText('Open Map Editor')
            button.clicked.connect(self.map_editor.show)
            self.setIndexWidget(index, button)

            self.model.layoutChanged.emit()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle('Map Key Exists')
            msg.setText('A Map key already exists in the tree.')
            msg.exec()


class MapDictionaryTreeModel(DictionaryTreeModel):
    def flags(self, index=QModelIndex()):
        if not index.isValid():
            return Qt.NoItemFlags

        # Disable editing values of keys with children and map keys
        item = self.getItem(index)
        if (index.column() != 0 and item.childItems) or item.data(0) == 'Map':
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable


class MapEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('map_editor.ui', self)

        self.selected_tile = None

        # Close window on Escape
        shortcut_close = QtWidgets.QShortcut(QKeySequence('Escape'), self)
        shortcut_close.activated.connect(self.close)

        self.tile_layout = self.findChild(QtWidgets.QGridLayout, 'gridLayout')

        # Add center tile
        self.add_tile()

    def add_tile(self, tile=None):
        # Replace tile if one is passed in
        if tile:
            tile_row, tile_col, _ = self.get_tile_position(tile)
            tile.deleteLater()
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
                                           (-1, 0),         (1, 0),
                                           (-1, 1), (0, 1), (1, 1)]:
            row = tile_row + neighbor_row
            col = tile_col + neighbor_col

            item = self.tile_layout.itemAtPosition(row, col)
            if not item:
                button = TileButton(self)
                self.tile_layout.addWidget(button, row, col)

    def remove_tile(self, tile):
        row, col, index = self.get_tile_position(tile)
        self.tile_layout.takeAt(index)
        tile.deleteLater()

        button = TileButton(self)
        self.tile_layout.addWidget(button, row, col)

        self.reshape()

    def reshape(self):
        # Loop over tile layout
        for row in range(self.tile_layout.rowCount()):
            for col in range(self.tile_layout.columnCount()):
                item = self.tile_layout.itemAtPosition(row, col)

                # If item is TileButton
                if item and isinstance(item.widget(), TileButton):
                    neighborless = True

                    # Loop over neighbors
                    for rel_col, rel_row in [(-1,-1), (0,-1), (1,-1),
                                             (-1, 0),         (1, 0),
                                             (-1, 1), (0, 1), (1, 1)]:
                        neighbor_row = row + rel_row
                        neighbor_col = col + rel_col

                        neighbor = self.tile_layout.itemAtPosition(neighbor_row, neighbor_col)

                        # If neighbor is TileLabel
                        if neighbor and isinstance(neighbor.widget(), TileLabel):
                            # TileButton isn't without neighbors
                            neighborless = False
                            break

                    if neighborless:
                        # Delete neighborless buttons
                        item.widget().deleteLater()

    def get_tile_position(self, tile):
        index = self.tile_layout.indexOf(tile)
        row, col, *_ = self.tile_layout.getItemPosition(index)

        return row, col, index


class TileLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.editor = TileEditor(self)

        # Right click context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setStyleSheet('QLabel { border: 2px solid #000 }')

    def open_menu(self, position):
        menu = QtWidgets.QMenu()

        edit_tile_action = menu.addAction('Edit Tile')
        edit_tile_action.triggered.connect(self.editor.show)

        remove_tile_action = menu.addAction('Remove Tile')
        remove_tile_action.triggered.connect(partial(self.parent.remove_tile, self))

        menu.exec(self.mapToGlobal(position))

    def mouseDoubleClickEvent(self, e):
        self.editor.show()


class TileEditor(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('tile_editor.ui', self)

        self.tree_view = self.findChild(DictionaryTreeView, 'treeView')
        self.state = self.tree_view.toDict()

        self.finished.connect(self.finish)

    def finish(self, result):
        # Rollback state if Cancel was clicked or Escape was pressed
        if not result:
            self.tree_view.setData(self.state)

    def showEvent(self, e):
        super().showEvent(e)

        # "Backup" tree view state
        self.state = self.tree_view.toDict()


class TileButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setText('...')

        self.clicked.connect(partial(parent.add_tile, self))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('fusion')
    editor = Editor()
    editor.show()
    sys.exit(app.exec())
