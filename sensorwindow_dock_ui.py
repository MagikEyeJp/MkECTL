# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sensorwindow_dock.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox, QComboBox,
    QDockWidget, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTextEdit, QToolButton, QVBoxLayout, QWidget)

from ImageViewScene import ImageViewer
import resources_rc

class Ui_sensor(object):
    def setupUi(self, sensor):
        if not sensor.objectName():
            sensor.setObjectName(u"sensor")
        sensor.resize(933, 946)
        sensor.setFloating(False)
        sensor.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetFloatable)
        sensor.setAllowedAreas(Qt.RightDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.horizontalLayout_3 = QHBoxLayout(self.dockWidgetContents)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.sensorImage = ImageViewer(self.dockWidgetContents)
        self.sensorImage.setObjectName(u"sensorImage")
        self.sensorImage.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.sensorImage.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.sensorImage.setInteractive(False)

        self.verticalLayout_5.addWidget(self.sensorImage)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.cameraStatusLabel = QLabel(self.dockWidgetContents)
        self.cameraStatusLabel.setObjectName(u"cameraStatusLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cameraStatusLabel.sizePolicy().hasHeightForWidth())
        self.cameraStatusLabel.setSizePolicy(sizePolicy)
        self.cameraStatusLabel.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.cameraStatusLabel)

        self.smoothingCheckBox = QCheckBox(self.dockWidgetContents)
        self.smoothingCheckBox.setObjectName(u"smoothingCheckBox")
        self.smoothingCheckBox.setChecked(True)

        self.horizontalLayout_2.addWidget(self.smoothingCheckBox)

        self.statsButton = QPushButton(self.dockWidgetContents)
        self.statsButton.setObjectName(u"statsButton")
        icon = QIcon()
        icon.addFile(u":/GUI_icons/labo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.statsButton.setIcon(icon)
        self.statsButton.setFlat(False)

        self.horizontalLayout_2.addWidget(self.statsButton)

        self.homeButton = QPushButton(self.dockWidgetContents)
        self.homeButton.setObjectName(u"homeButton")
        icon1 = QIcon()
        icon1.addFile(u":/GUI_icons/001-home.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.homeButton.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.homeButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.verticalLayout_5.setStretch(0, 1)

        self.horizontalLayout_3.addLayout(self.verticalLayout_5)

        self.SensorControlScrollArea = QScrollArea(self.dockWidgetContents)
        self.SensorControlScrollArea.setObjectName(u"SensorControlScrollArea")
        self.SensorControlScrollArea.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.SensorControlScrollArea.sizePolicy().hasHeightForWidth())
        self.SensorControlScrollArea.setSizePolicy(sizePolicy1)
        self.SensorControlScrollArea.setMinimumSize(QSize(260, 0))
        self.SensorControlScrollArea.setMaximumSize(QSize(260, 16777215))
        self.SensorControlScrollArea.setStyleSheet(u"#SensorControlScrollArea {\n"
"	border: none;\n"
"}\n"
"\n"
"QGroupBox[objectName^=\"Section\"] {\n"
"    font: bold; \n"
"    border: 1px solid silver;\n"
"    border-radius: 6px;\n"
"    margin-top: 6px;\n"
"}\n"
"\n"
"QGroupBox[objectName^=\"Section\"]::title {\n"
"    subcontrol-origin:  margin;\n"
"    left: 7px;\n"
"    padding: 0 5px 0 6px;\n"
"}\n"
"\n"
"\n"
"QScrollBar {\n"
"	border: 0px solid #999999;\n"
"   	background: lightgray;\n"
" 	width:10px;    \n"
"   	margin: 0px 0px 0px 0px;\n"
"}\n"
"\n"
"QScrollBar::handle {         \n"
"	min-height: 0px;\n"
"   	border: 0px solid red;\n"
"	border-radius: 5px;\n"
"	background-color: darkgray;\n"
"}\n"
"\n"
"QScrollBar::add-line:vertical {       \n"
" 	height: 0px;\n"
"	subcontrol-position: bottom;\n"
"	subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:vertical {\n"
"	height: 0 px;\n"
"	subcontrol-position: top;\n"
"	subcontrol-origin: margin;\n"
"}\n"
"")
        self.SensorControlScrollArea.setFrameShape(QFrame.StyledPanel)
        self.SensorControlScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.SensorControlScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.SensorControlScrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.SensorControlScrollArea.setWidgetResizable(False)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 240, 880))
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy2)
        self.scrollAreaWidgetContents.setMinimumSize(QSize(0, 0))
        self.layoutWidget = QWidget(self.scrollAreaWidgetContents)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(0, 0, 251, 3000))
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setSpacing(12)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.SectionSensorConnection = QGroupBox(self.layoutWidget)
        self.SectionSensorConnection.setObjectName(u"SectionSensorConnection")
        self.SectionSensorConnection.setMinimumSize(QSize(240, 190))
        self.SectionSensorConnection.setMaximumSize(QSize(240, 16777215))
        self.layoutWidget1 = QWidget(self.SectionSensorConnection)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(10, 30, 221, 151))
        self.verticalLayout_sc0 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_sc0.setObjectName(u"verticalLayout_sc0")
        self.verticalLayout_sc0.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_sc0.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_sc0 = QHBoxLayout()
        self.horizontalLayout_sc0.setObjectName(u"horizontalLayout_sc0")
        self.horizontalLayout_sc0.setSizeConstraint(QLayout.SetFixedSize)
        self.connectButton = QPushButton(self.layoutWidget1)
        self.connectButton.setObjectName(u"connectButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(5)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.connectButton.sizePolicy().hasHeightForWidth())
        self.connectButton.setSizePolicy(sizePolicy3)
        palette = QPalette()
        brush = QBrush(QColor(0, 0, 0, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        brush1 = QBrush(QColor(78, 154, 6, 255))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, brush1)
        brush2 = QBrush(QColor(255, 227, 186, 255))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Light, brush2)
        brush3 = QBrush(QColor(253, 201, 124, 255))
        brush3.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Midlight, brush3)
        brush4 = QBrush(QColor(126, 87, 31, 255))
        brush4.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark, brush4)
        brush5 = QBrush(QColor(168, 117, 41, 255))
        brush5.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid, brush5)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        brush6 = QBrush(QColor(255, 255, 255, 255))
        brush6.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText, brush6)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush6)
        brush7 = QBrush(QColor(252, 175, 62, 255))
        brush7.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush7)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Shadow, brush)
        brush8 = QBrush(QColor(253, 215, 158, 255))
        brush8.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, brush8)
        brush9 = QBrush(QColor(255, 255, 220, 255))
        brush9.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, brush9)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, brush)
        brush10 = QBrush(QColor(0, 0, 0, 128))
        brush10.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush10)
#endif
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Light, brush2)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Midlight, brush3)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Dark, brush4)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Mid, brush5)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.BrightText, brush6)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush6)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush7)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Shadow, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, brush8)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, brush9)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush10)
#endif
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush4)
        brush11 = QBrush(QColor(186, 189, 182, 255))
        brush11.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, brush11)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Light, brush2)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Midlight, brush3)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Dark, brush4)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Mid, brush5)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush4)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, brush6)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, brush4)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush7)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, brush7)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Shadow, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, brush7)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, brush9)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush10)
#endif
        self.connectButton.setPalette(palette)

        self.horizontalLayout_sc0.addWidget(self.connectButton)

        self.searchButton = QPushButton(self.layoutWidget1)
        self.searchButton.setObjectName(u"searchButton")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(1)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.searchButton.sizePolicy().hasHeightForWidth())
        self.searchButton.setSizePolicy(sizePolicy4)
        self.searchButton.setBaseSize(QSize(0, 0))
        icon2 = QIcon()
        icon2.addFile(u":/GUI_icons/135-search.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.searchButton.setIcon(icon2)

        self.horizontalLayout_sc0.addWidget(self.searchButton)


        self.verticalLayout_sc0.addLayout(self.horizontalLayout_sc0)

        self.horizontalLayout_sc1 = QHBoxLayout()
        self.horizontalLayout_sc1.setObjectName(u"horizontalLayout_sc1")
        self.horizontalLayout_sc1.setSizeConstraint(QLayout.SetFixedSize)
        self.horizontalLayout_sc1.setContentsMargins(-1, -1, -1, 0)
        self.labelAddr = QLabel(self.layoutWidget1)
        self.labelAddr.setObjectName(u"labelAddr")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(1)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.labelAddr.sizePolicy().hasHeightForWidth())
        self.labelAddr.setSizePolicy(sizePolicy5)

        self.horizontalLayout_sc1.addWidget(self.labelAddr)

        self.IPComboBox = QComboBox(self.layoutWidget1)
        self.IPComboBox.setObjectName(u"IPComboBox")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(5)
        sizePolicy6.setVerticalStretch(1)
        sizePolicy6.setHeightForWidth(self.IPComboBox.sizePolicy().hasHeightForWidth())
        self.IPComboBox.setSizePolicy(sizePolicy6)
        self.IPComboBox.setEditable(True)
        self.IPComboBox.setMaxCount(10)
        self.IPComboBox.setInsertPolicy(QComboBox.InsertAtTop)

        self.horizontalLayout_sc1.addWidget(self.IPComboBox)


        self.verticalLayout_sc0.addLayout(self.horizontalLayout_sc1)

        self.horizontalLayout_sc2 = QHBoxLayout()
        self.horizontalLayout_sc2.setObjectName(u"horizontalLayout_sc2")
        self.horizontalLayout_sc2.setSizeConstraint(QLayout.SetFixedSize)
        self.horizontalLayout_sc2.setContentsMargins(0, 0, -1, 0)
        self.labelSMID = QLabel(self.layoutWidget1)
        self.labelSMID.setObjectName(u"labelSMID")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(1)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.labelSMID.sizePolicy().hasHeightForWidth())
        self.labelSMID.setSizePolicy(sizePolicy7)

        self.horizontalLayout_sc2.addWidget(self.labelSMID)

        self.textSerial = QTextEdit(self.layoutWidget1)
        self.textSerial.setObjectName(u"textSerial")
        sizePolicy6.setHeightForWidth(self.textSerial.sizePolicy().hasHeightForWidth())
        self.textSerial.setSizePolicy(sizePolicy6)
        self.textSerial.setMinimumSize(QSize(0, 48))
        self.textSerial.setMaximumSize(QSize(16777215, 48))
        palette1 = QPalette()
        brush12 = QBrush(QColor(238, 238, 236, 255))
        brush12.setStyle(Qt.BrushStyle.SolidPattern)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush12)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush12)
        brush13 = QBrush(QColor(239, 239, 239, 255))
        brush13.setStyle(Qt.BrushStyle.SolidPattern)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush13)
        self.textSerial.setPalette(palette1)
        self.textSerial.setAutoFillBackground(False)
        self.textSerial.setReadOnly(True)

        self.horizontalLayout_sc2.addWidget(self.textSerial)

        self.horizontalLayout_sc2.setStretch(1, 2)

        self.verticalLayout_sc0.addLayout(self.horizontalLayout_sc2)

        self.horizontalLayout_sc3 = QHBoxLayout()
        self.horizontalLayout_sc3.setObjectName(u"horizontalLayout_sc3")
        self.horizontalLayout_sc3.setSizeConstraint(QLayout.SetFixedSize)
        self.horizontalLayout_sc3.setContentsMargins(-1, -1, -1, 0)
        self.labelLBLID = QLabel(self.layoutWidget1)
        self.labelLBLID.setObjectName(u"labelLBLID")
        sizePolicy7.setHeightForWidth(self.labelLBLID.sizePolicy().hasHeightForWidth())
        self.labelLBLID.setSizePolicy(sizePolicy7)

        self.horizontalLayout_sc3.addWidget(self.labelLBLID)

        self.textLabelID = QLineEdit(self.layoutWidget1)
        self.textLabelID.setObjectName(u"textLabelID")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy8.setHorizontalStretch(5)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.textLabelID.sizePolicy().hasHeightForWidth())
        self.textLabelID.setSizePolicy(sizePolicy8)
        self.textLabelID.setMinimumSize(QSize(0, 24))
        self.textLabelID.setMaximumSize(QSize(16777215, 24))
        self.textLabelID.setReadOnly(True)

        self.horizontalLayout_sc3.addWidget(self.textLabelID)

        self.smidDicEditBtn = QToolButton(self.layoutWidget1)
        self.smidDicEditBtn.setObjectName(u"smidDicEditBtn")
        icon3 = QIcon()
        icon3.addFile(u":/GUI_icons/pen.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.smidDicEditBtn.setIcon(icon3)

        self.horizontalLayout_sc3.addWidget(self.smidDicEditBtn)


        self.verticalLayout_sc0.addLayout(self.horizontalLayout_sc3)


        self.verticalLayout_3.addWidget(self.SectionSensorConnection)

        self.SectionCameraControl = QGroupBox(self.layoutWidget)
        self.SectionCameraControl.setObjectName(u"SectionCameraControl")
        self.SectionCameraControl.setEnabled(False)
        self.SectionCameraControl.setMinimumSize(QSize(240, 260))
        self.SectionCameraControl.setMaximumSize(QSize(240, 16777215))
        self.SectionCameraControl.setStyleSheet(u"QGroupBox:enabled{border-color:#66AAFF; border-width:2px}")
        self.previewGroup = QGroupBox(self.SectionCameraControl)
        self.previewGroup.setObjectName(u"previewGroup")
        self.previewGroup.setGeometry(QRect(10, 119, 91, 71))
        self.prev1Button = QPushButton(self.previewGroup)
        self.prev1Button.setObjectName(u"prev1Button")
        self.prev1Button.setGeometry(QRect(10, 30, 31, 31))
        icon4 = QIcon()
        icon4.addFile(u":/GUI_icons/014-image.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.prev1Button.setIcon(icon4)
        self.prevAveButton = QPushButton(self.previewGroup)
        self.prevAveButton.setObjectName(u"prevAveButton")
        self.prevAveButton.setGeometry(QRect(50, 30, 31, 31))
        icon5 = QIcon()
        icon5.addFile(u":/GUI_icons/015-images.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.prevAveButton.setIcon(icon5)
        self.consecutiveModeButton = QPushButton(self.previewGroup)
        self.consecutiveModeButton.setObjectName(u"consecutiveModeButton")
        self.consecutiveModeButton.setGeometry(QRect(60, 0, 20, 20))
        self.consecutiveModeButton.setStyleSheet(u"QPushButton:checked{background-color:orange}")
        icon6 = QIcon()
        icon6.addFile(u":/GUI_icons/133-spinner11.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.consecutiveModeButton.setIcon(icon6)
        self.consecutiveModeButton.setCheckable(True)
        self.preview_save_Group = QGroupBox(self.SectionCameraControl)
        self.preview_save_Group.setObjectName(u"preview_save_Group")
        self.preview_save_Group.setGeometry(QRect(110, 120, 121, 71))
        self.saveAveButton = QPushButton(self.preview_save_Group)
        self.saveAveButton.setObjectName(u"saveAveButton")
        self.saveAveButton.setGeometry(QRect(45, 30, 31, 31))
        self.saveAveButton.setIcon(icon5)
        self.save1Button = QPushButton(self.preview_save_Group)
        self.save1Button.setObjectName(u"save1Button")
        self.save1Button.setGeometry(QRect(8, 30, 31, 31))
        self.save1Button.setIcon(icon4)
        self.frameButton = QPushButton(self.preview_save_Group)
        self.frameButton.setObjectName(u"frameButton")
        self.frameButton.setGeometry(QRect(83, 30, 31, 31))
        self.frameButton.setMaximumSize(QSize(50, 16777215))
        self.layoutWidget2 = QWidget(self.SectionCameraControl)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(10, 30, 211, 91))
        self.formLayout = QFormLayout(self.layoutWidget2)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.shutterLabel = QLabel(self.layoutWidget2)
        self.shutterLabel.setObjectName(u"shutterLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.shutterLabel)

        self.shutterLineEdit = QLineEdit(self.layoutWidget2)
        self.shutterLineEdit.setObjectName(u"shutterLineEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.shutterLineEdit)

        self.framesLabel = QLabel(self.layoutWidget2)
        self.framesLabel.setObjectName(u"framesLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.framesLabel)

        self.framesLineEdit = QLineEdit(self.layoutWidget2)
        self.framesLineEdit.setObjectName(u"framesLineEdit")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.framesLineEdit)

        self.ISOlabel = QLabel(self.layoutWidget2)
        self.ISOlabel.setObjectName(u"ISOlabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.ISOlabel)

        self.ISOcombo = QComboBox(self.layoutWidget2)
        self.ISOcombo.addItem("")
        self.ISOcombo.addItem("")
        self.ISOcombo.addItem("")
        self.ISOcombo.addItem("")
        self.ISOcombo.addItem("")
        self.ISOcombo.addItem("")
        self.ISOcombo.setObjectName(u"ISOcombo")
        self.ISOcombo.setEditable(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.ISOcombo)

        self.selectDirectoryButton = QToolButton(self.SectionCameraControl)
        self.selectDirectoryButton.setObjectName(u"selectDirectoryButton")
        self.selectDirectoryButton.setGeometry(QRect(200, 200, 26, 21))
        icon7 = QIcon()
        icon7.addFile(u":/GUI_icons/049-folder-open.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.selectDirectoryButton.setIcon(icon7)
        self.saveDirecoryName = QLabel(self.SectionCameraControl)
        self.saveDirecoryName.setObjectName(u"saveDirecoryName")
        self.saveDirecoryName.setGeometry(QRect(10, 200, 181, 20))
        self.saveDirecoryName.setFrameShape(QFrame.StyledPanel)
        self.saveDirecoryName.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.saveImgName = QLabel(self.SectionCameraControl)
        self.saveImgName.setObjectName(u"saveImgName")
        self.saveImgName.setGeometry(QRect(10, 230, 181, 20))
        self.saveImgName.setFrameShape(QFrame.StyledPanel)
        self.saveImgName.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.resetButton = QPushButton(self.SectionCameraControl)
        self.resetButton.setObjectName(u"resetButton")
        self.resetButton.setGeometry(QRect(200, 226, 26, 24))
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.resetButton.sizePolicy().hasHeightForWidth())
        self.resetButton.setSizePolicy(sizePolicy9)
        self.resetButton.setIcon(icon6)

        self.verticalLayout_3.addWidget(self.SectionCameraControl)

        self.SectionLaserControl = QGroupBox(self.layoutWidget)
        self.SectionLaserControl.setObjectName(u"SectionLaserControl")
        self.SectionLaserControl.setEnabled(False)
        self.SectionLaserControl.setMinimumSize(QSize(240, 148))
        self.SectionLaserControl.setMaximumSize(QSize(240, 16777215))
        self.SectionLaserControl.setStyleSheet(u"QGroupBox:enabled{border-color:#66AAFF; border-width:2px}")
        self.evenLaserButton = QPushButton(self.SectionLaserControl)
        self.evenLaserButton.setObjectName(u"evenLaserButton")
        self.evenLaserButton.setGeometry(QRect(10, 30, 61, 25))
        self.evenLaserButton.setCheckable(True)
        self.evenLaserButton.setAutoExclusive(True)
        self.oddLaserButton = QPushButton(self.SectionLaserControl)
        self.oddLaserButton.setObjectName(u"oddLaserButton")
        self.oddLaserButton.setGeometry(QRect(70, 30, 61, 25))
        self.oddLaserButton.setCheckable(True)
        self.oddLaserButton.setAutoExclusive(True)
        self.onAllLaserButton = QPushButton(self.SectionLaserControl)
        self.onAllLaserButton.setObjectName(u"onAllLaserButton")
        self.onAllLaserButton.setGeometry(QRect(130, 30, 41, 25))
        icon8 = QIcon()
        icon8.addFile(u":/GUI_icons/lightON.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.onAllLaserButton.setIcon(icon8)
        self.onAllLaserButton.setCheckable(True)
        self.onAllLaserButton.setAutoExclusive(True)
        self.offAllLaserButton = QPushButton(self.SectionLaserControl)
        self.offAllLaserButton.setObjectName(u"offAllLaserButton")
        self.offAllLaserButton.setGeometry(QRect(170, 30, 41, 25))
        icon9 = QIcon()
        icon9.addFile(u":/GUI_icons/lightOFF.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.offAllLaserButton.setIcon(icon9)
        self.offAllLaserButton.setCheckable(True)
        self.offAllLaserButton.setAutoExclusive(True)
        self.hex4dLineEdit = QLineEdit(self.SectionLaserControl)
        self.hex4dLineEdit.setObjectName(u"hex4dLineEdit")
        self.hex4dLineEdit.setEnabled(False)
        self.hex4dLineEdit.setGeometry(QRect(90, 70, 91, 25))
        self.hex4dCheckBox = QCheckBox(self.SectionLaserControl)
        self.hex4dCheckBox.setObjectName(u"hex4dCheckBox")
        self.hex4dCheckBox.setGeometry(QRect(20, 70, 61, 23))
        self.hex4dCheckBox.setAutoExclusive(True)
        self.setHex4dLaserButton = QPushButton(self.SectionLaserControl)
        self.setHex4dLaserButton.setObjectName(u"setHex4dLaserButton")
        self.setHex4dLaserButton.setEnabled(False)
        self.setHex4dLaserButton.setGeometry(QRect(190, 70, 31, 25))
        icon10 = QIcon()
        icon10.addFile(u":/GUI_icons/exec.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.setHex4dLaserButton.setIcon(icon10)
        self.CurrentLaserPattern_label = QLabel(self.SectionLaserControl)
        self.CurrentLaserPattern_label.setObjectName(u"CurrentLaserPattern_label")
        self.CurrentLaserPattern_label.setGeometry(QRect(10, 100, 221, 17))
        self.CurrentLaserPattern_value = QLabel(self.SectionLaserControl)
        self.CurrentLaserPattern_value.setObjectName(u"CurrentLaserPattern_value")
        self.CurrentLaserPattern_value.setGeometry(QRect(10, 120, 211, 20))
        self.CurrentLaserPattern_value.setFrameShape(QFrame.StyledPanel)
        self.CurrentLaserPattern_value.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.SectionLaserControl)

        self.SectionGrid = QGroupBox(self.layoutWidget)
        self.SectionGrid.setObjectName(u"SectionGrid")
        self.SectionGrid.setEnabled(False)
        self.SectionGrid.setMinimumSize(QSize(240, 235))
        self.SectionGrid.setMaximumSize(QSize(240, 16777215))
        self.SectionGrid.setStyleSheet(u"QGroupBox:enabled:checked{border-color:#66AAFF; border-width:2px}\n"
"")
        self.SectionGrid.setCheckable(True)
        self.SectionGrid.setChecked(False)
        self.layoutWidget_2 = QWidget(self.SectionGrid)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(10, 30, 219, 201))
        self.formLayout_2 = QFormLayout(self.layoutWidget_2)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.typeLabel = QLabel(self.layoutWidget_2)
        self.typeLabel.setObjectName(u"typeLabel")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.typeLabel)

        self.gridTypeCombo = QComboBox(self.layoutWidget_2)
        self.gridTypeCombo.addItem("")
        self.gridTypeCombo.addItem("")
        self.gridTypeCombo.addItem("")
        self.gridTypeCombo.addItem("")
        self.gridTypeCombo.setObjectName(u"gridTypeCombo")
        self.gridTypeCombo.setEditable(True)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.gridTypeCombo)

        self.linesLabel = QLabel(self.layoutWidget_2)
        self.linesLabel.setObjectName(u"linesLabel")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.linesLabel)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.xlabel = QLabel(self.layoutWidget_2)
        self.xlabel.setObjectName(u"xlabel")

        self.horizontalLayout_9.addWidget(self.xlabel)

        self.xLineEdit = QLineEdit(self.layoutWidget_2)
        self.xLineEdit.setObjectName(u"xLineEdit")

        self.horizontalLayout_9.addWidget(self.xLineEdit)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.ylabel = QLabel(self.layoutWidget_2)
        self.ylabel.setObjectName(u"ylabel")

        self.horizontalLayout_6.addWidget(self.ylabel)

        self.yLineEdit = QLineEdit(self.layoutWidget_2)
        self.yLineEdit.setObjectName(u"yLineEdit")

        self.horizontalLayout_6.addWidget(self.yLineEdit)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_6)


        self.formLayout_2.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_5)

        self.rotLabel = QLabel(self.layoutWidget_2)
        self.rotLabel.setObjectName(u"rotLabel")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.rotLabel)

        self.rotLineEdit = QLineEdit(self.layoutWidget_2)
        self.rotLineEdit.setObjectName(u"rotLineEdit")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.rotLineEdit)

        self.gridColorLabel = QLabel(self.layoutWidget_2)
        self.gridColorLabel.setObjectName(u"gridColorLabel")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.gridColorLabel)

        self.gridColorCombo = QComboBox(self.layoutWidget_2)
        self.gridColorCombo.addItem("")
        self.gridColorCombo.addItem("")
        self.gridColorCombo.addItem("")
        self.gridColorCombo.addItem("")
        self.gridColorCombo.addItem("")
        self.gridColorCombo.addItem("")
        self.gridColorCombo.setObjectName(u"gridColorCombo")
        self.gridColorCombo.setEditable(True)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.gridColorCombo)

        self.offsetLabel = QLabel(self.layoutWidget_2)
        self.offsetLabel.setObjectName(u"offsetLabel")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.offsetLabel)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.xlabel_2 = QLabel(self.layoutWidget_2)
        self.xlabel_2.setObjectName(u"xlabel_2")

        self.horizontalLayout_11.addWidget(self.xlabel_2)

        self.xOffsetLineEdit = QLineEdit(self.layoutWidget_2)
        self.xOffsetLineEdit.setObjectName(u"xOffsetLineEdit")

        self.horizontalLayout_11.addWidget(self.xOffsetLineEdit)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.ylabel_2 = QLabel(self.layoutWidget_2)
        self.ylabel_2.setObjectName(u"ylabel_2")

        self.horizontalLayout_12.addWidget(self.ylabel_2)

        self.yOffsetLineEdit = QLineEdit(self.layoutWidget_2)
        self.yOffsetLineEdit.setObjectName(u"yOffsetLineEdit")

        self.horizontalLayout_12.addWidget(self.yOffsetLineEdit)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_12)


        self.formLayout_2.setLayout(4, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_10)

        self.alpha = QLabel(self.layoutWidget_2)
        self.alpha.setObjectName(u"alpha")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.LabelRole, self.alpha)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.alphaLineEdit = QLineEdit(self.layoutWidget_2)
        self.alphaLineEdit.setObjectName(u"alphaLineEdit")

        self.horizontalLayout_14.addWidget(self.alphaLineEdit)

        self.percentLabel = QLabel(self.layoutWidget_2)
        self.percentLabel.setObjectName(u"percentLabel")

        self.horizontalLayout_14.addWidget(self.percentLabel)


        self.horizontalLayout_13.addLayout(self.horizontalLayout_14)


        self.formLayout_2.setLayout(5, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_13)


        self.verticalLayout_3.addWidget(self.SectionGrid)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.SensorControlScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_3.addWidget(self.SensorControlScrollArea)

        sensor.setWidget(self.dockWidgetContents)

        self.retranslateUi(sensor)

        QMetaObject.connectSlotsByName(sensor)
    # setupUi

    def retranslateUi(self, sensor):
        sensor.setWindowTitle(QCoreApplication.translate("sensor", u"Sensor Window", None))
        self.cameraStatusLabel.setText(QCoreApplication.translate("sensor", u"CAMERA STATE", None))
        self.smoothingCheckBox.setText(QCoreApplication.translate("sensor", u"Smooth", None))
        self.statsButton.setText("")
        self.homeButton.setText("")
        self.SectionSensorConnection.setTitle(QCoreApplication.translate("sensor", u"Sensor Connection", None))
        self.connectButton.setText(QCoreApplication.translate("sensor", u"Connect", None))
        self.searchButton.setText("")
        self.labelAddr.setText(QCoreApplication.translate("sensor", u"Addr", None))
        self.IPComboBox.setCurrentText(QCoreApplication.translate("sensor", u"127.0.0.1", None))
        self.labelSMID.setText(QCoreApplication.translate("sensor", u"SMID", None))
        self.labelLBLID.setText(QCoreApplication.translate("sensor", u"LBLID", None))
        self.textLabelID.setText("")
        self.smidDicEditBtn.setText(QCoreApplication.translate("sensor", u"...", None))
        self.SectionCameraControl.setTitle(QCoreApplication.translate("sensor", u"Camera Control", None))
        self.previewGroup.setTitle(QCoreApplication.translate("sensor", u"Preview", None))
        self.prev1Button.setText("")
        self.prevAveButton.setText("")
        self.consecutiveModeButton.setText("")
        self.preview_save_Group.setTitle(QCoreApplication.translate("sensor", u"Save", None))
        self.saveAveButton.setText("")
        self.save1Button.setText("")
        self.frameButton.setText(QCoreApplication.translate("sensor", u"3D", None))
        self.shutterLabel.setText(QCoreApplication.translate("sensor", u"Shutter [us]", None))
        self.shutterLineEdit.setText("")
        self.framesLabel.setText(QCoreApplication.translate("sensor", u"#~frames", None))
        self.framesLineEdit.setText("")
        self.ISOlabel.setText(QCoreApplication.translate("sensor", u"ISO", None))
        self.ISOcombo.setItemText(0, QCoreApplication.translate("sensor", u"100", None))
        self.ISOcombo.setItemText(1, QCoreApplication.translate("sensor", u"200", None))
        self.ISOcombo.setItemText(2, QCoreApplication.translate("sensor", u"400", None))
        self.ISOcombo.setItemText(3, QCoreApplication.translate("sensor", u"800", None))
        self.ISOcombo.setItemText(4, QCoreApplication.translate("sensor", u"1600", None))
        self.ISOcombo.setItemText(5, QCoreApplication.translate("sensor", u"3200", None))

        self.selectDirectoryButton.setText(QCoreApplication.translate("sensor", u"...", None))
        self.saveDirecoryName.setText("")
        self.saveImgName.setText("")
        self.resetButton.setText("")
        self.SectionLaserControl.setTitle(QCoreApplication.translate("sensor", u"Laser Control", None))
        self.evenLaserButton.setText(QCoreApplication.translate("sensor", u"EVEN", None))
        self.oddLaserButton.setText(QCoreApplication.translate("sensor", u"ODD", None))
        self.onAllLaserButton.setText("")
        self.offAllLaserButton.setText("")
        self.hex4dCheckBox.setText(QCoreApplication.translate("sensor", u"Hex", None))
        self.setHex4dLaserButton.setText("")
        self.CurrentLaserPattern_label.setText(QCoreApplication.translate("sensor", u"Current Laser Pattern(No.1-16):", None))
        self.CurrentLaserPattern_value.setText("")
        self.SectionGrid.setTitle(QCoreApplication.translate("sensor", u"Grid", None))
        self.typeLabel.setText(QCoreApplication.translate("sensor", u"Type", None))
        self.gridTypeCombo.setItemText(0, QCoreApplication.translate("sensor", u"Solid", None))
        self.gridTypeCombo.setItemText(1, QCoreApplication.translate("sensor", u"Dot", None))
        self.gridTypeCombo.setItemText(2, QCoreApplication.translate("sensor", u"Dash", None))
        self.gridTypeCombo.setItemText(3, QCoreApplication.translate("sensor", u"DashDot", None))

        self.linesLabel.setText(QCoreApplication.translate("sensor", u"Lines", None))
        self.xlabel.setText(QCoreApplication.translate("sensor", u"x:", None))
        self.xLineEdit.setText(QCoreApplication.translate("sensor", u"3", None))
        self.ylabel.setText(QCoreApplication.translate("sensor", u"y:", None))
        self.yLineEdit.setText(QCoreApplication.translate("sensor", u"3", None))
        self.rotLabel.setText(QCoreApplication.translate("sensor", u"Rot", None))
        self.rotLineEdit.setText(QCoreApplication.translate("sensor", u"0.0", None))
        self.gridColorLabel.setText(QCoreApplication.translate("sensor", u"Color", None))
        self.gridColorCombo.setItemText(0, QCoreApplication.translate("sensor", u"Bright", None))
        self.gridColorCombo.setItemText(1, QCoreApplication.translate("sensor", u"Dark", None))
        self.gridColorCombo.setItemText(2, QCoreApplication.translate("sensor", u"Red", None))
        self.gridColorCombo.setItemText(3, QCoreApplication.translate("sensor", u"Blue", None))
        self.gridColorCombo.setItemText(4, QCoreApplication.translate("sensor", u"Green", None))
        self.gridColorCombo.setItemText(5, QCoreApplication.translate("sensor", u"Yellow", None))

        self.offsetLabel.setText(QCoreApplication.translate("sensor", u"Offset", None))
        self.xlabel_2.setText(QCoreApplication.translate("sensor", u"x:", None))
        self.xOffsetLineEdit.setText(QCoreApplication.translate("sensor", u"0.0", None))
        self.ylabel_2.setText(QCoreApplication.translate("sensor", u"y:", None))
        self.yOffsetLineEdit.setText(QCoreApplication.translate("sensor", u"0.0", None))
        self.alpha.setText(QCoreApplication.translate("sensor", u"alpha", None))
        self.alphaLineEdit.setText(QCoreApplication.translate("sensor", u"50", None))
        self.percentLabel.setText(QCoreApplication.translate("sensor", u"%", None))
    # retranslateUi

