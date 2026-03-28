from .Qt.QtCore import Qt, QEvent
from .Qt.QtCore import QStandardPaths
from krita import Krita
import types

from .Qt.QtWidgets import QCheckBox

major_ver = int(Krita.instance().version().split('.')[0])

Qt_Enum = types.SimpleNamespace()
Qt_Enum.CheckState = None
Qt_Enum.WindowType = None
Qt_Enum.MouseButton = None
Qt_Enum.AlignmentFlag = None
Qt_Enum.Orientation = None
Qt_Enum.Key = None

QEvent_Enum = types.SimpleNamespace()
QEvent_Enum.Type = None

QStandardPaths_Enum = types.SimpleNamespace()
QStandardPaths_Enum.StandardLocation = None

Qt_QOpenGLWidget = None

Q5t6_QCheckBox = None

if major_ver >= 6:
    Qt_Enum.CheckState = Qt.CheckState
    Qt_Enum.WindowType = Qt.WindowType
    Qt_Enum.MouseButton = Qt.MouseButton
    Qt_Enum.AlignmentFlag = Qt.AlignmentFlag
    Qt_Enum.Orientation = Qt.Orientation
    Qt_Enum.Key = Qt.Key

    QEvent_Enum.Type = QEvent.Type

    QStandardPaths_Enum.StandardLocation = QStandardPaths.StandardLocation
    
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    Qt_QOpenGLWidget = QOpenGLWidget

    Q5t6_QCheckBox = QCheckBox

else:
    Qt_Enum.CheckState = Qt
    Qt_Enum.WindowType = Qt
    Qt_Enum.MouseButton = Qt
    Qt_Enum.AlignmentFlag = Qt
    Qt_Enum.Orientation = Qt
    Qt_Enum.Key = Qt

    QEvent_Enum.Type = QEvent
    
    QStandardPaths_Enum.StandardLocation = QStandardPaths
    
    from PyQt5.QtWidgets import QOpenGLWidget
    Qt_QOpenGLWidget = QOpenGLWidget

    Q5t6_QCheckBox = QCheckBox
    Q5t6_QCheckBox.checkStateChanged = QCheckBox.stateChanged
