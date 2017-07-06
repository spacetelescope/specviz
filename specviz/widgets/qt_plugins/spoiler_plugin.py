from qtpy import QtGui, QtDesigner
from ..spoiler import Spoiler


class SpoilerPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent=None):
        super(SpoilerPlugin, self).__init__(self)

        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return Spoiler(parent)

    def name(self):
        return "Spoiler"

    def group(self):
        return "Custom Widgets"

    def icon(self):
        return QtGui.QIcon()

    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False

    def domXml(self):
        return ("""
<widget class="Spoiler" name="spoiler">
    <property name="toolTip" >
        <string>The current time</string>
    </property>
    <property name="whatsThis" >
        <string>The analog clock widget displays the current time.</string>
    </property>
</widget>
""")

    def includeFile(self):
        return "..spoiler"