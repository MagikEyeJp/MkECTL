# -*- coding:utf-8 -*-

# Reference: http://melpystudio.blog82.fc2.com/blog-entry-138.html
# Other page: https://gist.github.com/mieki256/1b73aae707cee97fffab544af9bc0637
#            https://mfumi.hatenadiary.org/entry/20141112/1415806010
import sys
from math import pow
from PyQt5 import QtWidgets, QtGui, QtCore

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


# /////////////////////////////////////////////////////////////////////////////
# ビューを表示するためのシーン。                                             //
# /////////////////////////////////////////////////////////////////////////////
class ImageViewScene(QtWidgets.QGraphicsScene):
    def __init__(self, *argv, **keywords):
        super(ImageViewScene, self).__init__(*argv, **keywords)
        self.__imageItem = None
        self.__currentPos = None
        self.__pressedButton = None

    def setPixMap(self, pixmap):
        # 既にシーンにPixmapアイテムがある場合は削除する。
        if self.__imageItem:
            self.removeItem(self.__imageItem)

        # 与えられたイメージをPixmapアイテムとしてシーンに追加する。-----------
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        # アイテムを移動可能アイテムとして設定。
        item.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
        )
        self.addItem(item)
        self.__imageItem = item
        # ---------------------------------------------------------------------

        self.fitImage()

        return pixmap

    def setFile(self, filepath):
        # イメージをアイテムとしてシーンに追加するためのメソッド。
        pixmap = QtGui.QPixmap(filepath)

        # 既にシーンにPixmapアイテムがある場合は削除する。
        if self.__imageItem:
            self.removeItem(self.__imageItem)

        # 与えられたイメージをPixmapアイテムとしてシーンに追加する。-----------
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        # アイテムを移動可能アイテムとして設定。
        item.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
        )
        self.addItem(item)
        self.__imageItem = item
        # ---------------------------------------------------------------------

        self.fitImage()

        return pixmap

    def imageItem(self):
        return self.__imageItem

    def fitImage(self):
        # イメージをシーンのサイズに合わせてフィットするためのメソッド。
        # アスペクト比によって縦にフィットするか横にフィットするかを自動的に
        # 決定する。
        if not self.imageItem():
            return

        # イメージの元の大きさを持つRectオブジェクト。
        boundingRect = self.imageItem().boundingRect()
        # シーンの現在の大きさを持つRectオブジェクト。
        sceneRect = self.sceneRect()

        itemAspectRatio = boundingRect.width() / boundingRect.height()
        sceneAspectRatio = sceneRect.width() / sceneRect.height()

        # 最終的にイメージのアイテムに適応するためのTransformオブジェクト。
        transform = QtGui.QTransform()

        if itemAspectRatio >= sceneAspectRatio:
            # 横幅に合わせてフィット。
            scaleRatio = sceneRect.width() / boundingRect.width()
        else:
            # 縦の高さに合わせてフィット。.
            scaleRatio = sceneRect.height() / boundingRect.height()

        # アスペクト比からスケール比を割り出しTransformオブジェクトに適応。
        transform.scale(scaleRatio, scaleRatio)
        # 変換されたTransformオブジェクトをイメージアイテムに適応。
        self.imageItem().setTransform(transform)

    def mouseDoubleClickEvent(self, event):
        self.fitImage()

    # マウスのドラッグ中の処理イベント。=======================================
    def mousePressEvent(self, event):
        self.__currentPos = event.scenePos()
        self.__pressedButton = event.button()

        if self.__pressedButton == QtCore.Qt.RightButton:
            cursorShape = QtCore.Qt.SizeAllCursor
        else:
            cursorShape = QtCore.Qt.ClosedHandCursor
        QtWidgets.qApp.setOverrideCursor(QtGui.QCursor(cursorShape))

    def mouseMoveEvent(self, event):
        if not self.__currentPos:
            return

        # シーンの現在位置。
        cur = event.scenePos()

        value = cur - self.__currentPos
        self.__currentPos = cur

        # 最終的に適応するTransformオブジェクト。
        transform = self.imageItem().transform()

        # 現在のシーン上のマウスカーソル位置情報から、イメージアイテム上での
        # マウスカーソル位置を示すTransformオブジェクトを呼び出す。
        localTrs = self.imageItem().mapFromScene(cur)

        if self.__pressedButton == QtCore.Qt.RightButton:
            # 右ボタンでドラッグされた場合はスケール処理を実行。
            if value.x() < 0:
                value = 0.9
            else:
                value = 1.1

            # マウスカーソル位置を中心にスケールするように変換を実行。
            transform.translate(localTrs.x(), localTrs.y()) \
                .scale(value, value) \
                .translate(-localTrs.x(), -localTrs.y())
        else:
            # それ以外のボタンでドラッグされた場合は移動処理を実行。
            transform *= QtGui.QTransform().translate(value.x(), value.y())

        # 最終的に変換されたTransformオブジェクトを
        # イメージオブジェクトへ適応する。
        self.imageItem().setTransform(transform)

    def mouseReleaseEvent(self, event):
        self.__currentPos = None
        self.__pressedButton = None
        QtWidgets.qApp.restoreOverrideCursor()
        super(ImageViewScene, self).mouseReleaseEvent(event)

    # =========================================================================

    def addScrollBarValue(self, dx, dy):
        """ スクロールバーの現在値を変化させる """
        x = self.horizontalScrollBar().value()
        y = self.verticalScrollBar().value()
        self.horizontalScrollBar().setValue(x + dx)
        self.verticalScrollBar().setValue(y + dy)

    def getMousePos(self, event, msg):
        """ マウス座標を取得 """
        x = event.pos().x()
        y = event.pos().y()

        kind = ""
        if event.buttons() & QtCore.Qt.LeftButton:
            kind = "Left "
        if event.button() & QtCore.Qt.MidButton:
            kind += "Mid "
        if event.button() & QtCore.Qt.RightButton:
            kind += "Right "

        global status
        status.showMessage("(%d , %d) %s %s" % (x, y, kind, msg))
        return event.pos()

    def scrollContentsBy(self, dx, dy):
        """ スクロールバー操作時に呼ばれる処理 """
        # スクロール中、Scene内にブラシがあると何故かゴミが残るので、
        # ブラシを非表示にしてからスクロールさせている。
        # self.scene().setVisibleBrush(False)
        super(ImageViewScene, self).scrollContentsBy(dx, dy)

    def changeZoomRatio(self, d):
        """ 外部から与えられた値でズーム変更 """
        v = self.changeZoomValue(math.pow(1.2, d)) / 100.0
        self.resetMatrix()
        self.scale(v, v)
        # self.setSceneNewRect()

    def changeZoomValue(self, d):
        """ ズーム率の変数を変更 """
        global zoomValue
        return self.clipZoomValue(zoomValue * d)

    def clipZoomValue(self, zv):
        global zoomDisp
        global zoomValue
        zoomValue = max(10, min(zv, 3200))  # 10 - 3200の範囲にする
        zvi = int(zoomValue)
        zoomDisp.setText("%5d%s" % (zvi, '%'))
        return zvi

    def fitZoom(self):
        """ ウインドウサイズに合わせてズーム変更 """
        cr = self.scene().sceneRect()
        vr = self.viewport().rect()
        ax = float(vr.width()) * 100.0 / float(cr.width())
        ay = float(vr.height()) * 100.0 / float(cr.height())
        if ax <= ay:
            # 横方向で合わせる
            zv = ax
        else:
            # 縦方向で合わせる
            zv = ay

        v = self.clipZoomValue(zv) / 100.0
        self.resetMatrix()
        self.scale(v, v)

    def zoomActualPixels(self):
        """ 等倍表示 """
        v = self.clipZoomValue(100) / 100.0
        self.resetMatrix()
        self.scale(v, v)


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
# メインとなるビュー。                                                       //
# /////////////////////////////////////////////////////////////////////////////
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

    def setPixMap(self, pixmap):
        self.m_pixmapitem.setPixmap(pixmap)
        if self.m_pixmapitem.boundingRect() != self.m_pixmaprect:
            self.m_pixmaprect = self.m_pixmapitem.boundingRect()
            # self.pixSizeChanged.emit(self.m_pixmaprect)
        if self.m_fitmode:
            self.scaleFit()

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
            m_scale = self.width() / self.m_scene.itemsBoundingRect().width()
        self.m_fitmode = True

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(256, 256)

    def setFile(self, filepath):
        # ビューが持つシーンにファイルパスを渡して初期化処理を
        # 実行するメソッド。
        self.scene().setFile(filepath)

    def resizeEvent(self, event):
        # ビューをリサイズ時にシーンの矩形を更新する。
        print("resize")
        if self.m_fitmode:
            self.scaleFit()

        super(ImageViewer, self).resizeEvent(event)
        # self.scene().setSceneRect(QtCore.QRectF(self.rect()))

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


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    viewer = ImageViewer()
    # QGraphicsSceneにイメージパスをセットする。
    viewer.setFile(imagepath)
    viewer.show()

    sys.exit(app.exec_())
