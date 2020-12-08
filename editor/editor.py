#!/usr/bin/env python3

import sys
import json
from functools import partial
from pprint import pprint

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

    def buildMenu(self, position):
        menu = super().buildMenu(position)

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

        # Close window on Escape
        shortcut_close = QtWidgets.QShortcut(QKeySequence('Escape'), self)
        shortcut_close.activated.connect(self.close)

        # Set graphics scene
        view = self.findChild(QtWidgets.QGraphicsView, 'graphicsView')
        self.scene = QtWidgets.QGraphicsScene(self)
        view.setScene(self.scene)

        # Initialize 3x3 grid
        self.map = Map(self.scene)
        self.map.add_tile(0, 0)

    def showEvent(self, e):
        super().showEvent(e)
        self.map.draw_grid()


class Map:
    def __init__(self, scene):
        self.scene = scene
        self.grid = [[None]]
        self.num_rows = 1
        self.num_cols = 1
        self.center_x = 0
        self.center_y = 0

    def draw_grid(self):
        for row in self.grid:
            for tile in row:
                if tile:
                    widget = tile.widget()
                    x = (widget.x * widget.width()) + (widget.x * 5)
                    y = (widget.y * widget.height()) + (widget.y * 5)
                    tile.setPos(x, y)

    def add_tile(self, x, y):
        tile = TileLabel(x, y, self)

        # Normalize position
        x += self.center_x
        y += self.center_y

        # Expand grid horizontally (left)
        if x == 0:
            for row in range(self.num_rows):
                self.grid[row].insert(0, None)

            # Adjust column values
            self.num_cols += 1
            self.center_x += 1
            x += 1

        # Expand grid horizontally (right)
        if x == self.num_cols - 1:
            for row in range(self.num_rows):
                self.grid[row].append(None)
            self.num_cols += 1

        # Expand grid vertically (top)
        if y == 0:
            self.grid.insert(0, [None] * self.num_cols)

            # Adjust row values
            self.num_rows += 1
            self.center_y += 1
            y += 1

        # Expand grid vertically (bottom)
        if y == self.num_rows - 1:
            self.grid.append([None] * self.num_cols)
            self.num_rows += 1

        self.grid[y][x] = self.scene.addWidget(tile)
        self.add_neighbors(x, y)

        self.draw_grid()

    def remove_tile(self, x, y):
        button = TileButton(x, y, self)

        # Normalize position
        x += self.center_x
        y += self.center_y

        # Remove tile label from grid
        tile = self.grid[y][x]
        pprint(self.grid)
        print(f'delete item at {x}, {y}')
        #self.scene.removeItem(tile)
        tile.setZValue(-999)
        tile.widget().hide()
        tile.widget().deleteLater()
        del tile

        # Replace with button
        self.grid[y][x] = self.scene.addWidget(button)

        # Reshape grid
        self.reshape()

        # Update tile positions
        self.draw_grid()

    def reshape(self):
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                tile = self.grid[y][x]

                if tile and isinstance(tile.widget(), TileButton):
                    neighborless = True
                    for rel_x, rel_y in [(-1,-1), (0,-1), (1,-1),
                                         (-1, 0),         (1, 0),
                                         (-1, 1), (0, 1), (1, 1)]:
                        abs_x = x + rel_x
                        abs_y = y + rel_y

                        # Bounds check
                        if not (0 <= abs_x < self.num_cols) or not (0 <= abs_y < self.num_rows):
                            continue

                        neighbor = self.grid[abs_y][abs_x]

                        if neighbor and isinstance(neighbor.widget(), TileLabel):
                            neighborless = False
                            break

                    if neighborless:
                        # Remove tile button from grid
                        pprint(self.grid)
                        print(f'delete item at {x}, {y}')
                        #self.scene.removeItem(tile)
                        tile.setZValue(-999)
                        tile.widget().hide()
                        tile.deleteLater()
                        del tile
                        self.grid[y][x] = None

        # Check top row
        if all(tile is None for tile in self.grid[0]):
            self.grid.pop(0)
            self.num_rows -= 1
            self.center_y -= 1

        # Check bottom row
        if all(tile is None for tile in self.grid[self.num_rows - 1]):
            self.grid.pop(self.num_rows - 1)
            self.num_rows -= 1

        # Check left column
        if all(row[0] is None for row in self.grid):
            for row in self.grid:
                row.pop(0)
            self.num_cols -= 1
            self.center_x -= 1

        # Check right column
        if all(row[self.num_cols - 1] is None for row in self.grid):
            for row in self.grid:
                row.pop(self.num_cols - 1)
            self.num_cols -= 1

        print(self.num_rows, self.num_cols)

    def add_neighbors(self, x, y):
        tile = self.grid[y][x]

        for rel_x, rel_y in [(-1,-1), (0,-1), (1,-1),
                             (-1, 0),         (1, 0),
                             (-1, 1), (0, 1), (1, 1)]:
            abs_x = x + rel_x
            abs_y = y + rel_y
            neighbor = self.grid[abs_y][abs_x]

            if not neighbor:
                button = TileButton(tile.widget().x + rel_x, tile.widget().y + rel_y, self)
                self.grid[abs_y][abs_x] = self.scene.addWidget(button)


class TileLabel(QtWidgets.QLabel):
    def __init__(self, x, y, parent=None):
        super().__init__()

        self.x = x
        self.y = y
        self.parent = parent
        self.editor = TileEditor()

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setStyleSheet('QLabel { border: 2px solid #000 }')

    def open_menu(self, position):
        menu = QtWidgets.QMenu()

        edit_tile_action = menu.addAction('Edit Tile')
        edit_tile_action.triggered.connect(self.editor.show)

        remove_tile_action = menu.addAction('Remove Tile')
        remove_tile_action.triggered.connect(partial(self.parent.remove_tile, self.x, self.y))

        menu.exec(self.mapToGlobal(position))

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.open_menu(e.pos())
        else:
            super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.editor.show()
        else:
            super().mouseDoubleClickEvent(e)


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
    def __init__(self, x, y, parent=None):
        super().__init__()

        self.x = x
        self.y = y

        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.setText('...')

        self.clicked.connect(partial(parent.add_tile, self.x, self.y))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('fusion')
    editor = Editor()
    editor.show()
    sys.exit(app.exec())
