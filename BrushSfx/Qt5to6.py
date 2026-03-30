from .Qt.QtCore import Qt, QEvent
from .Qt.QtCore import QStandardPaths
from krita import Krita
from .Qt.QtWidgets import QCheckBox

major_ver = int(Krita.instance().version().split('.')[0])

Qt_QOpenGLWidget = None


if major_ver >= 6:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    Qt_QOpenGLWidget = QOpenGLWidget
else:
    from PyQt5.QtWidgets import QOpenGLWidget
    Qt_QOpenGLWidget = QOpenGLWidget
    QCheckBox.checkStateChanged = QCheckBox.stateChanged


def getEventPosition(event):
    if major_ver >= 6:
        return event.position().toPoint()
    else:
        return event.pos()