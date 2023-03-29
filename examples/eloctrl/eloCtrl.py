import time

from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QMenuBar,
    QStatusBar,
    QFrame,
    QMainWindow,
    QLabel,
    QPushButton,
    QLineEdit,
    QDoubleSpinBox,
    QCheckBox,
    QToolButton,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSpacerItem,
    QDialog,
    QDialogButtonBox
)
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import setupRange
from time import sleep
import sys
from pyfea import Fea
import pyfea.errors
from LedIndicatorWidget import LedIndicator

SIM = False

class SetupRangeWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = setupRange.Ui_rangeSetup()
        self.ui.setupUi(self)
        self.ui.buttonBox.button(QDialogButtonBox.YesToAll).clicked.connect(self.yesToAllClicked)

    def yesToAllClicked(self):
        self.setResult(2)
        pass



class SetupButton(QToolButton):
    def __init__(self):
        super(SetupButton, self).__init__()
        self.setIcon(QtGui.QIcon("gear-icon.png"))


class StatusLed(LedIndicator):
    def __init__(self, parent=None):
        LedIndicator.__init__(self, parent)
        self.setDisabled(True)
        self.setFixedSize(16, 16)

    def setRed(self):
        self.onColor1 = QColor(255, 0, 0)
        self.onColor2 = QColor(192, 0, 0)
        self.offColor1 = QColor(28, 0, 0)
        self.offColor2 = QColor(128, 0, 0)
        self.update()

    def setGreen(self):
        self.onColor1 = QColor(0, 255, 0)
        self.onColor2 = QColor(0, 192, 0)
        self.offColor1 = QColor(0, 28, 0)
        self.offColor2 = QColor(0, 128, 0)
        self.update()

class TopBar(QFrame):
    def __init__(self, parent, fea: pyfea.Fea):
        super(TopBar, self).__init__(parent)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.fea = fea

        self.openButton = QPushButton("Open")

        self.enableAllInstruments = QPushButton("Enable all inst.")
        self.enableAllInstruments.clicked.connect(parent.enableAllInstruments)
        self.enableAll = QPushButton("Enable all")
        self.enableAll.clicked.connect(parent.enableAll)
        self.disableAllInstruments = QPushButton("Disable all")
        self.disableAllInstruments.clicked.connect(parent.disableAllInstruments)
        self.exitButton = QPushButton("Quit")

        self.visaNameEdit = QLineEdit()

        self.horizontalLayout.addWidget(QLabel("VISA Name:"))
        self.horizontalLayout.addWidget(self.visaNameEdit)
        self.horizontalLayout.addWidget(self.openButton)
        self.horizontalLayout.addWidget(self.enableAllInstruments)
        self.horizontalLayout.addWidget(self.enableAll)
        self.horizontalLayout.addWidget(self.disableAllInstruments)
        self.horizontalLayout.addWidget(self.exitButton)


class ChannelPanel(QFrame):
    def __init__(self, parent, number):
        super(ChannelPanel, self).__init__()

        self.channelNumber = number

        self.setParent(parent)
        self.grid = QVBoxLayout(self)
        self.instrument = None

        self.frame1 = QFrame(self)
        self.frame1layout = QHBoxLayout(self.frame1)
        self.grid.addWidget(self.frame1)
        self.frame1layout.setContentsMargins(0, 0, 0, 0)

        self.frame2 = QFrame(self)
        self.frame2layout = QHBoxLayout(self.frame2)
        self.frame2layout.setContentsMargins(0, 0, 0, 0)


        self.nameLabel = QLabel("%d" % self.channelNumber)
        #self.nameLabel.setAlignment(QtCore.Qt.AlignHCenter)
        font = self.nameLabel.font()
        font.setPixelSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.nameLabel.setFont(font)


        self.enableCB = QCheckBox("Enable")
        self.enableCB.clicked.connect(self.enableChanged)

        self.status = StatusLed()

        self.frame1layout.addWidget(self.nameLabel)
        self.frame1layout.addWidget(self.enableCB)
        self.frame1layout.addWidget(self.status)

        self.setpoint = QDoubleSpinBox()
        self.setpoint.setMaximum(5000)
        self.setpoint.setMinimum(-5000)
        self.setpoint.valueChanged.connect(self.valueChanged)

        self.rangeButton = SetupButton()
        self.rangeButton.clicked.connect(self.setupRange)

        self.frame2layout.addWidget(self.setpoint)
        self.frame2layout.addWidget(self.rangeButton)

        self.grid.addWidget(self.frame2)


        self.meters = QLabel("-")
        self.meters.setAlignment(QtCore.Qt.AlignHCenter)
        self.grid.addWidget(self.meters)

        #self.grid.addItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
        #                                        QtWidgets.QSizePolicy.Expanding), 5, 0, 1, 2)

    def setInstrument(self, instrument:pyfea.Instrument):
        self.instrument = instrument

    def enableChanged(self):
        if self.enableCB.isChecked():
            self.instrument.turn_on_channels(self.channelNumber)
            self.valueChanged()

        else:
            self.instrument.turn_off_channels(self.channelNumber)

    def setupRange(self):
        dialog = SetupRangeWindow()
        rangeLow,rangeHigh = self.instrument.get_range(self.channelNumber)
        dialog.ui.lowRange.setValue(rangeLow)
        dialog.ui.highRange.setValue(rangeHigh)
        result = dialog.exec()
        if result == 1:
            self.instrument.set_range(self.channelNumber, dialog.ui.lowRange.value(), dialog.ui.highRange.value())
        elif result == 2:
            for channel in self.instrument.channels:
                self.instrument.set_range(channel, dialog.ui.lowRange.value(), dialog.ui.highRange.value())


    def valueChanged(self):
        try:
            value = float(self.setpoint.value())
        except:
            return
        self.instrument.set_voltage(self.channelNumber, value)


class InstrumentPanel(QFrame):
    def __init__(self, parent, instrument : pyfea.Instrument):
        super(InstrumentPanel, self).__init__()

        self.instrument = instrument
        self.channelPanels = []

        self.setParent(parent)
        self.grid = QVBoxLayout(self)
        self.setFixedWidth(150)
        self.setFrameShape(QFrame.Box)

        self.frame1 = QFrame(self)
        self.frame1layout = QHBoxLayout(self.frame1)
        self.frame1layout.setContentsMargins(0, 0, 0, 0)
        self.grid.addWidget(self.frame1)

        self.nameLabel = QLabel(self.instrument.name)
        self.nameLabel.setAlignment(QtCore.Qt.AlignHCenter)
        font = self.nameLabel.font()
        font.setBold(True)
        font.setWeight(75)
        font.setPixelSize(16)
        self.nameLabel.setFont(font)

        self.enableCB = QCheckBox("Enable")
        self.enableCB.stateChanged.connect(self.enableChanged)
        #self.enableCB.setChecked(instrument.get_state())
        self.status = StatusLed()

        self.frame1layout.addWidget(self.nameLabel)
        self.frame1layout.addWidget(self.enableCB)
        self.frame1layout.addWidget(self.status)

        self.serial_temperature = QLabel("-")
        self.serial_temperature.setAlignment(QtCore.Qt.AlignHCenter)
        self.grid.addWidget(self.serial_temperature)

        self.channels = QFrame(self)
        self.channelsLayout = QVBoxLayout(self.channels)
        self.channelsLayout.setContentsMargins(0, 0, 0, 0)
        self.grid.addWidget(self.channels)

        self.grid.addSpacerItem(QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                                QtWidgets.QSizePolicy.Expanding))

    def addChannelPanel(self, channelPanel : ChannelPanel):
        self.channelPanels.append(channelPanel)
        self.channelsLayout.addWidget(channelPanel)

    def setName(self, name):
        self.nameLabel.setText(name)

    def enableChanged(self):
        if self.enableCB.isChecked():
            self.instrument.turn_on(wait=False)
        else:
            self.instrument.turn_off(wait=False)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("FEA Control")
        self.resize(1150, 550)
        self.fea = Fea()

        self.centralWidget = QWidget(self)

        self.verticalLayout = QVBoxLayout(self.centralWidget)

        self.topBar = TopBar(self, self.fea)
        self.topBar.openButton.clicked.connect(self.open_close_click)
        self.topBar.exitButton.clicked.connect(self.close)

        self.verticalLayout.addWidget(self.topBar)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setFrameShape(QFrame.Box)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = QWidget()

        self.horizontalLayout = QHBoxLayout(self.scrollAreaWidgetContents)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.setCentralWidget(self.centralWidget)

        self.menuBar = QMenuBar(self)
        self.setMenuBar(self.menuBar)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.instrumentPanels = []

        if SIM:
            for i in range(1, 4):
                self.fea._instruments.append(pyfea.Aps(self.fea, i, "APS %d" % i))

        self.populate_instrument_box()

        #self.stepLabel = QLabel("Long-Running Step: 0")
        #self.stepLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        #self.longRunningBtn = QPushButton("Long-Running Task!", self)
        #self.longRunningBtn.clicked.connect(self.runBackgroundTask)
        #self.topBar.horizontalLayout.addWidget(self.stepLabel)
        #self.topBar.horizontalLayout.addWidget(self.longRunningBtn)

        self.runBackgroundTask()

    def clear_instrument_box(self):
        pass

    def populate_instrument_box(self):
        self.clear_instrument_box()

        for instrument in self.fea._instruments:
            panel = InstrumentPanel(self, instrument)
            self.instrumentPanels.append(panel)
            self.horizontalLayout.addWidget(panel)

            channelPanel = ChannelPanel(panel, 1)
            channelPanel.setInstrument(instrument)
            panel.addChannelPanel(channelPanel)
            channelPanel.setpoint.setValue(instrument.get_voltage())

        self.horizontalLayout.addSpacerItem(
            QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

    def set_visa_name(self, visa_name):
        self.topBar.visaNameEdit.setText(visa_name)

    def get_visa_name(self):
        return self.topBar.visaNameEdit.text()

    def open_close_click(self):
        if self.fea.is_opened():
            self.fea.close()
            self.topBar.openButton.setText("Open")
            self.clear_instrument_box()
            self.statusBar.showMessage("Connection with %s closed" % self.get_visa_name())
        else:
            try:
                self.fea.open(self.get_visa_name())
                self.statusBar.showMessage("Connection with %s opened" % self.get_visa_name())
            except pyfea.errors.VISAError:
                self.statusBar.showMessage("Connection with %s not successful" % self.get_visa_name())
                return
            self.topBar.openButton.setText("Close")
            self.populate_instrument_box()

    def enableAllInstruments(self):
        for instrument in self.fea._instruments:
            instrument.turn_on(wait=False)

    def disableAllInstruments(self):
        for instrument in self.fea._instruments:
            instrument.turn_off(wait=False)

    def enableAll(self):
        self.enableAllInstruments()
        self.fea.wait_for_operation_complete()

        for instPanel in self.instrumentPanels:
            for channelPanel in instPanel.channelPanels:
                instPanel.instrument.turn_on_channels(channelPanel.channelNumber)
                #time.sleep(0.1)
                value = float(channelPanel.setpoint.value())
                instPanel.instrument.set_voltage(channelPanel.channelNumber, value)

    def runBackgroundTask(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.setParentWindow(self)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def setParentWindow(self, parentWindow: MainWindow):
        self.parentWindow = parentWindow

    def run(self):
        i = 0
        while True:
            for instrument, instrumentPanel in zip(self.parentWindow.fea._instruments, self.parentWindow.instrumentPanels):
                state = instrument.get_state()
                instrumentPanel.enableCB.setChecked(state)
                instrumentPanel.status.setChecked(state)
                instrumentPanel.serial_temperature.setText("%s, %5.2f °C" %
                                                           (instrument.get_serial(), instrument.get_temperature()))
                voltages = instrument.measure_voltage()
                currents = instrument.measure_current()

                for channel, channelPanel, voltage, current in \
                        zip(instrument.channels, instrumentPanel.channelPanels, voltages, currents):

                    state = instrument.get_channels_state(channel)[0]
                    ready = instrument.is_ready(channel)

                    channelPanel.enableCB.setChecked(state)
                    channelPanel.meters.setText("%6.1fV/%6.1fµA" % (voltage, current * 1e6))

                    channelPanel.status.setChecked(state)

                    if state:
                        if ready:
                            channelPanel.status.setGreen()
                        else:
                            channelPanel.status.setRed()
                    else:
                        channelPanel.status.setGreen()
            sleep(0.05)
            i += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("elo.ico"))
    window = MainWindow()
    #window.set_visa_name('TCPIP0::172.17.170.75::hislip0::INSTR')
    #window.set_visa_name('TCPIP0::192.168.0.60::hislip0::INSTR')
    window.set_visa_name('GPIB::22::INSTR')
    window.open_close_click()
    window.show()
    app.exec()


