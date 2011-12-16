# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

from cadnano import app
from pathview.colorpanel import ColorPanel
from pathview.tools.pathtoolmanager import PathToolManager
from sliceview.slicerootitem import SliceRootItem
from pathview.pathrootitem import PathRootItem

from sliceview.tools.slicetoolmanager import SliceToolManager
import ui.mainwindow.ui_mainwindow as ui_mainwindow
import util

util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'Qt', 'QFileInfo',
                                        'QPoint', 'QSettings', 'QSize',
                                        'QString'])
util.qtWrapImport('QtGui', globals(), ['QAction', 'QApplication',
                                       'QGraphicsObject', 'QGraphicsScene',
                                       'QGraphicsView', 'QMainWindow',
                                       'QGraphicsItem', 'QGraphicsRectItem',
                                       'QWidget', 'QPaintEngine'])
# for OpenGL mode
try:
    from OpenGL import GL
except:
    GL = False

GL = False

class DocumentWindow(QMainWindow, ui_mainwindow.Ui_MainWindow):
    """docstring for DocumentWindow"""
    def __init__(self, parent=None, docCtrlr=None):
        super(DocumentWindow, self).__init__(parent)
        self.controller = docCtrlr
        doc = docCtrlr.document()
        self.setupUi(self)
        self.settings = QSettings()
        self._readSettings()
        # Slice setup
        self.slicescene = QGraphicsScene(parent=self.sliceGraphicsView)
        self.sliceroot = SliceRootItem(rect=self.slicescene.sceneRect(),\
                                       parent=None,\
                                       window=self,\
                                       document=doc)
        self.sliceroot.setFlag(QGraphicsItem.ItemHasNoContents)
        self.slicescene.addItem(self.sliceroot)
        assert self.sliceroot.scene() == self.slicescene
        self.sliceGraphicsView.setScene(self.slicescene)
        self.sliceGraphicsView.sceneRootItem = self.sliceroot
        self.sliceGraphicsView.setName("SliceView")
        self.sliceToolManager = SliceToolManager(self)
        # Path setup
        self.pathscene = QGraphicsScene(parent=self.pathGraphicsView)
        self.pathroot = PathRootItem(rect=self.pathscene.sceneRect(),\
                                     parent=None,\
                                     window=self,\
                                     document=doc)
        self.pathroot.setFlag(QGraphicsItem.ItemHasNoContents)
        self.pathscene.addItem(self.pathroot)
        assert self.pathroot.scene() == self.pathscene
        self.pathGraphicsView.setScene(self.pathscene)
        self.pathGraphicsView.sceneRootItem = self.pathroot
        self.pathGraphicsView.setScaleFitFactor(0.9)
        self.pathGraphicsView.setName("PathView")
        self.pathColorPanel = ColorPanel()
        self.pathGraphicsView.toolbar = self.pathColorPanel  # HACK for customqgraphicsview
        self.pathscene.addItem(self.pathColorPanel)
        self.pathToolManager = PathToolManager(self)
        self.sliceToolManager.pathToolManager = self.pathToolManager
        self.pathToolManager.sliceToolManager = self.sliceToolManager
        
        # set the selection filter default
        doc.documentSelectionFilterChangedSignal.emit(["endpoint", "scaffold"])

        self.pathGraphicsView.setupGL()
        self.sliceGraphicsView.setupGL()
        if GL:
            pass
            # self.slicescene.drawBackground = self.drawBackgroundGL
            # self.pathscene.drawBackground = self.drawBackgroundGL

        if app().isInMaya():
            from solidview.solidrootitem import SolidRootItem
            self.splitter.setOrientation(Qt.Vertical)
            self.setUnifiedTitleAndToolBarOnMac(False)
            modState = self.actionModify.isChecked()
            self.solidroot = SolidRootItem(parent=None, document=doc,
                                           modState=modState)

        # Edit menu setup
        self.actionUndo = docCtrlr.undoStack().createUndoAction(self)
        self.actionRedo = docCtrlr.undoStack().createRedoAction(self)
        self.actionUndo.setText(QApplication.translate(
                                            "MainWindow", "Undo",
                                            None, QApplication.UnicodeUTF8))
        self.actionUndo.setShortcut(QApplication.translate(
                                            "MainWindow", "Ctrl+Z",
                                            None, QApplication.UnicodeUTF8))
        self.actionRedo.setText(QApplication.translate(
                                            "MainWindow", "Redo",
                                            None, QApplication.UnicodeUTF8))
        self.actionRedo.setShortcut(QApplication.translate(
                                            "MainWindow", "Ctrl+Shift+Z",
                                            None, QApplication.UnicodeUTF8))
        self.sep = QAction(self)
        self.sep.setSeparator(True)
        self.menuEdit.insertAction(self.actionCut, self.sep)
        self.menuEdit.insertAction(self.sep, self.actionRedo)
        self.menuEdit.insertAction(self.actionRedo, self.actionUndo)
        self.splitter.setSizes([400, 400])  # balance splitter size

    ### ACCESSORS ###
    def undoStack(self):
        return self.controller.undoStack()

    def selectedPart(self):
        return self.controller.document().selectedPart()

    ### EVENT HANDLERS ###
    def focusInEvent(self):
        app().undoGroup.setActiveStack(self.controller.undoStack())

    def moveEvent(self, event):
        """Reimplemented to save state on move."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

    def resizeEvent(self, event):
        """Reimplemented to save state on resize."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.endGroup()
        QWidget.resizeEvent(self, event)

    def changeEvent(self, event):
        QWidget.changeEvent(self, event)
    # end def

    ### DRAWING RELATED ###
    # def drawBackgroundGL(self, painter, rect):
    #     """
    #     This method is for overloading the QGraphicsScene.
    #     """
    #     if painter.paintEngine().type() != QPaintEngine.OpenGL and \
    #         painter.paintEngine().type() != QPaintEngine.OpenGL2:
    # 
    #         qWarning("OpenGLScene: drawBackground needs a QGLWidget to be set as viewport on the graphics view");
    #         return
    #     # end if
    #     painter.beginNativePainting()
    #     GL.glDisable(GL.GL_DEPTH_TEST) # disable for 2D drawing
    #     GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    #     GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    # 
    #     painter.endNativePainting()
    # # end def
    
    # def drawBackgroundNonGL(self, painter, rect):
    #     """
    #     This method is for overloading the QGraphicsScene.
    #     """
    #     print self
    #     return QGraphicsScene.drawBackground(self, painter, rect)
    # # end def

    ### PRIVATE HELPER METHODS ###
    def _readSettings(self):
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QSize(1100, 800)).toSize())
        self.move(self.settings.value("pos", QPoint(200, 200)).toPoint())
        self.settings.endGroup()

