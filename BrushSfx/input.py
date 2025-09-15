
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QObject, QEvent, QPoint
import time

class InputListener(QObject):
    def __init__(self):
        super().__init__()
        
        self.__is_pressing = False
        self.__cursor_potition = QPoint(0, 0)
        self.__last_cursor_position_read = QPoint(0, 0)
        self.__pressure = 0.0
        self.__is_tablet_input = False
        self.__last_tablet_input_time = time.time()
        
        self.__time_for_tablet = 0.1
        
    @property
    def is_tablet(self)-> bool:
        return self.__is_tablet_input

    @property
    def is_pressing(self) -> bool:
        return self.__is_pressing
    
    @property
    def pressure(self) -> float:
        return self.__pressure * self.__is_pressing
    
    @property
    def cursor_movement(self) -> float:
        """
        read only once per audio callback
        """
        movement = self.__last_cursor_position_read - self.__cursor_potition
        self.__last_cursor_position_read = self.__cursor_potition
        return movement

    def startListening():
        pass
    def stopListening():
        pass

    def eventFilter(self, obj, event):
        if obj.__class__ != QOpenGLWidget:
            return super().eventFilter(obj, event)
        if (self.__is_pressing):
            
            #position
            if (event.type() == QEvent.TabletMove or \
                event.type() == QEvent.MouseMove):
                self.__cursor_potition = event.pos()
                    
            #pressure
            if (event.type() == QEvent.TabletMove):
                self.__pressure = event.pressure()
                self.__last_tablet_input_time = time.time()
                self.__is_tablet_input = True

            if (event.type() == QEvent.MouseMove and time.time() >= self.__last_tablet_input_time + 0.1):
                self.__pressure = 1.0
                self.__is_tablet_input = False

        

        if (event.type() == QEvent.TabletPress or \
            event.type() == QEvent.MouseButtonPress) and \
            event.button()== Qt.LeftButton:
            self.__is_pressing = True
            self.__cursor_potition = event.pos()
            self.__last_cursor_position_read = event.pos()

        #releasing
        if (event.type() == QEvent.TabletRelease or \
            event.type() == QEvent.MouseButtonRelease) and \
            event.button()== Qt.LeftButton:
            self.__pressure = 0.0
            self.__is_pressing = False

        return super().eventFilter(obj, event)


input_listener = InputListener()