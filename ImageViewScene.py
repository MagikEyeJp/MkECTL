# -*- coding:utf-8 -*-

# Reference: http://melpystudio.blog82.fc2.com/blog-entry-138.html
# Other page: https://gist.github.com/mieki256/1b73aae707cee97fffab544af9bc0637
#            https://mfumi.hatenadiary.org/entry/20141112/1415806010
import sys
from math import pow
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen

ZOOMSCALE_MAX = 50.0
ZOOMSCALE_MIN = 0.05

imagepath = 'GUI_icons/keigan_icon.png'

canvasSize = (640, 480)
padding = 48

# ズーム倍率 (単位は%。floatを使うと誤差がたまるのでint(整数)で管理する)
zoomValue = 100

status = None
zoomDisp = None
gView = None
myApp = None

class ImageViewer(QtWidgets.QGraphicsView):
    def __init__(self, widget):
        super(ImageViewer, self).__init__()

        # QGraphicsViewの設定。------------------------------------------------
        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.setRenderHints(QtGui.QPainter.Antialiasing |
                            QtGui.QPainter.SmoothPixmapTransform |
                            QtGui.QPainter.TextAntialiasing
                            )
        # ---------------------------------------------------------------------

        # QGraphicsSceneの作成・および設定。------------------------------------
        # self.m_scene = ImageViewScene(self)
        self.m_scene = QtWidgets.QGraphicsScene()
        self.setScene(self.m_scene)
        self.m_pixmapitem = QtWidgets.QGraphicsPixmapItem()
        self.m_pixmapitem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.m_pixmaprect = QtCore.QRectF(0.0, 0.0, 0.0, 0.0)
        self.m_scene.addItem(self.m_pixmapitem)
        self.isPixmapSet = False

        self.m_gridItem = GridItem()
        self.gridParam = self.m_gridItem.GridParameter()

        # scene.setFile( imagepath )
        self.m_wheelzoom = False
        self.m_fitmode = True
        self.m_scale = 1.0
        # ---------------------------------------------------------------------
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.m_scene.addItem(self.m_gridItem)

        # stats mode display
        self.mode = "none"
        self.on_pixel_selected = None  # Callback function
        self._roi_rect = None
        self._pixel_marker = None

    def setPixMap(self, pixmap):
        self.m_pixmapitem.setPixmap(pixmap)
        if self.m_pixmapitem.boundingRect() != self.m_pixmaprect:
            self.m_pixmaprect = self.m_pixmapitem.boundingRect()
            # self.pixSizeChanged.emit(self.m_pixmaprect)
        if self.m_fitmode:
            self.scaleFit()
        self.isPixmapSet = True
    
    def getQImage(self):
        # QImageを取得するメソッド
        if self.m_pixmapitem.pixmap().isNull():
            return None
        else:
            return self.m_pixmapitem.pixmap().toImage()

    def setScale(self, scale, innter=False):
        self.resetTransform()
        self.scale(scale, scale)
        self.m_scale = scale
        # self.scaleChanged.emit (m_scale, m_wheelzoom)
        if not innter:
            self.m_wheelzoom = False
            self.m_fitmode = False

    def scaleFit(self):
        self.fitInView(self.m_scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        if self.m_scene.itemsBoundingRect().width() != 0:
            self.m_scale = self.width() / self.m_scene.itemsBoundingRect().width()
        self.m_fitmode = True

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(256, 256)

    def setFile(self, filepath):
        # ビューが持つシーンにファイルパスを渡して初期化処理を
        # 実行するメソッド。
        self.scene().setFile(filepath)

    def resizeEvent(self, event):
        # ビューをリサイズ時にシーンの矩形を更新する。
        # print("resize")
        self.m_fitmode = True
        if self.m_fitmode:
            self.scaleFit()
            # print('scaleFit')

        super(ImageViewer, self).resizeEvent(event)
        # self.scene().setSceneRect(QtCore.QRectF(self.rect()))

    def mousePressEvent(self, event):
        if self.mode == "pixel" and event.button() == Qt.LeftButton:
            scenepos = self.mapToScene(event.pos())
            itempos = self.m_pixmapitem.mapFromScene(scenepos)
            if QtCore.QRect(0,0, self.m_pixmapitem.pixmap().width(), self.m_pixmapitem.pixmap().height()).contains(itempos.toPoint()):
                x = int(itempos.x())
                y = int(itempos.y())

                # Draw red circle
                if self._pixel_marker:
                    self.m_scene.removeItem(self._pixel_marker)
                self._pixel_marker = QtWidgets.QGraphicsEllipseItem(x - 3, y - 3, 6, 6)
                pen = QPen(QColor(255, 0, 0))
                pen.setWidth(2)
                self._pixel_marker.setPen(pen)
                self._pixel_marker.setBrush(QBrush(Qt.NoBrush))  # ← 塗りつぶしなし
                self.m_scene.addItem(self._pixel_marker)

                # Callback
                if self.on_pixel_selected:
                    self.on_pixel_selected(x, y)
        super().mousePressEvent(event)


    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        self.m_wheelzoom = True
        scenepos = self.mapToScene(event.pos())
        if event.angleDelta() != 0:
            newscale = self.m_scale * pow(1.5, (event.angleDelta().y() / 120.0))
            if event.angleDelta().y() > 0:
                self.setScale(newscale if newscale < ZOOMSCALE_MAX else ZOOMSCALE_MAX)
            else:
                self.setScale(newscale if ZOOMSCALE_MIN < newscale else ZOOMSCALE_MIN)
            viewpos = self.mapFromScene(scenepos)
            move = viewpos - event.pos()
            self.horizontalScrollBar().setValue(move.x() + self.horizontalScrollBar().value())
            self.verticalScrollBar().setValue(move.y() + self.verticalScrollBar().value())

    def setGridVisible(self, visible: bool):
        m_gridvisible = visible
        self.m_gridItem.setVisible(m_gridvisible)

    def setGridParameter(self, p):
        print("setGridParameter")
        self.m_gridItem.makeGrid(self.m_pixmapitem.boundingRect(), p)
    
    def set_mode(self, mode: str):
        self.mode = mode
        self.clear_overlay()

        if mode == "roi":
            # ROI 矩形（仮固定、あとでドラッグ可能にする）
            self._roi_rect = QGraphicsRectItem(100, 100, 100, 100)
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            self._roi_rect.setPen(pen)
            self._roi_rect.setBrush(QBrush(Qt.NoBrush))
            self.scene.addItem(self._roi_rect)

        elif mode == "pixel":
            # Nothing until click
            pass

    def clear_overlay(self):
        if self._roi_rect:
            self.m_scene.removeItem(self._roi_rect)
            self._roi_rect = None
        if self._pixel_marker:
            self.m_scene.removeItem(self._pixel_marker)
            self._pixel_marker = None

    def get_roi_rect(self):
        """Returns ROI as (x, y, width, height), or None if not set."""
        if self._roi_rect:
            rect = self._roi_rect.rect()
            return (
                int(rect.x()),
                int(rect.y()),
                int(rect.width()),
                int(rect.height())
            )
        return None
        
# /////////////////////////////////////////////////////////////////////////////

class GridItem(QtWidgets.QGraphicsPathItem):
    def __init__(self):
        super(GridItem, self).__init__()

        self.path = QtGui.QPainterPath()
        # self.painter = QtGui.QPainter(self.sensorWindow)

        # self.painter.begin(self)


    def makeGrid(self, rect: QtCore.QRectF, param):

        self.resetTransform()

        # qDebug("GridItem::makeGrid %d x %d %f deg.\n", p.lines_x, p.lines_y, p.angle);
        path = self.path    # path - path ?
        # self.painter.setPen(param.pen)
        self.setPen(param.pen)
        # self.painter.setPen(QtCore.Qt.black)
        rect.translate(param.offset_x, param.offset_y)
        path.addRect(rect)
        step_x = rect.width() / (param.lines_x + 1)
        step_y = rect.height() / (param.lines_y + 1)

        for x in range(1, param.lines_x + 1):
            path.moveTo(x * step_x + param.offset_x, rect.top())
            path.lineTo(x * step_x + param.offset_x, rect.bottom())

        for y in range(1, param.lines_y + 1):
            path.moveTo(rect.left(), y * step_y + param.offset_y)
            path.lineTo(rect.right(), y * step_y + param.offset_y)

        self.setTransformOriginPoint(rect.center())
        self.setRotation(param.rot)
        self.setPath(path)
        path.clear()

    class GridParameter():
        def __init__(self):
            self.gridType = 'Solid'
            self.lines_x: int = 3
            self.lines_y: int = 3
            self.rot: float = 0.0

            self.color = 'Bright'
            self.alpha: float = 0.5
            self.colorDict: dict = {'Bright': (255, 255, 255),
                                    'Dark': (0, 0, 0),
                                    'Red': (255, 0, 0),
                                    'Blue': (0, 0, 255),
                                    'Green': (0, 255, 0),
                                    'Yellow': (255, 255, 0)}
            self.qcolor = QColor(*self.colorDict[self.color])  # unpack: https://note.nkmk.me/python-argument-expand/
            self.qcolor.setAlphaF(self.alpha)

            self.offset_x: float = 0.0
            self.offset_y: float = 0.0

            # pen styles: https://doc.qt.io/archives/qtjambi-4.5.2_01/com/trolltech/qt/core/Qt.PenStyle.html
            self.pen_styles: dict = {'Solid': QtCore.Qt.SolidLine,
                                     'Dot': QtCore.Qt.DotLine,
                                     'Dash': QtCore.Qt.DashLine,
                                     'DashDot': QtCore.Qt.DashDotLine}

            # self.pen = QPen(QColor(*self.colorDict[self.color]).setAlphaF(self.alpha))
            self.pen = QPen(self.qcolor)
            self.pen.setStyle(self.pen_styles[self.gridType])
            # self.pen = QPen(QColor('#0a64c8'))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    viewer = ImageViewer()
    # QGraphicsSceneにイメージパスをセットする。
    viewer.setFile(imagepath)
    viewer.show()

    sys.exit(app.exec())
