import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QRadioButton, QStackedWidget, \
                            QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt

class WidgetButtons(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        for i in range(4):
            layout.addWidget(QPushButton(f'Button #{i}'))

        self.setLayout(layout)

class WidgetLineEdits(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        for i in range(4):
            layout.addWidget(QLineEdit(f'LineEdit #{i}'))

        self.setLayout(layout)

class WidgetRadioButtons(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        for i in range(4):
            layout.addWidget(QRadioButton(f'RaidoButton #{i}'))

        self.setLayout(layout)

class AppDemo(QWidget):
    def __init__(self):
        super().__init__()

        mainLayout = QVBoxLayout()

        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(WidgetButtons()) # index 0
        self.stackedWidget.addWidget(WidgetLineEdits()) # index 1
        self.stackedWidget.addWidget(WidgetRadioButtons()) # index 2

        buttonPrevious = QPushButton('Previous')
        buttonPrevious.clicked.connect(self.previousWidget)

        buttonNext = QPushButton('Next')
        buttonNext.clicked.connect(self.nextWidget)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(buttonPrevious)
        buttonLayout.addWidget(buttonNext)

        mainLayout.addWidget(self.stackedWidget)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

    def nextWidget(self):
        self.stackedWidget.setCurrentIndex((self.stackedWidget.currentIndex() + 1) % 3)

    def previousWidget(self):
        self.stackedWidget.setCurrentIndex((self.stackedWidget.currentIndex() - 1) % 3)

app = QApplication(sys.argv)
demo = AppDemo()
demo.show()
sys.exit(app.exec_())
