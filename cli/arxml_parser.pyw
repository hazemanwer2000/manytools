
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.Base.TimeUtils as TimeUtils
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON

from pprint import pprint

class ElementQueryWidget(GElements.CustomWidget):
    
    def __init__(self):
        self.rootLayout = GElements.Layouts.GridLayout(3, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
        self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
        super().__init__(GElements.Widgets.Decorators.Outline(self.rootWidget, AbstractGraphics.SymmetricMargin(5)))
        
        # ? Create (sub-)widget(s).
        self.lineEdit_QueryPath = GElements.Widgets.Basics.LineEdit(placeholder='Element-Path', isEditable=True, isMonospaced=True)
        self.lineEdit_QueryType = GElements.Widgets.Basics.LineEdit(placeholder='Element-Type', isEditable=True, isMonospaced=True)
        self.button_Query = GElements.Widgets.Basics.Button(text='Query')
        
        # ? Set layout widget(s).
        rowIdx = -1
        self.rootLayout.setWidget(self.lineEdit_QueryPath, (rowIdx := rowIdx + 1), 0, colSpan=2)
        self.rootLayout.setWidget(self.lineEdit_QueryType, (rowIdx := rowIdx + 1), 0, colSpan=2)
        self.rootLayout.setWidget(self.button_Query, (rowIdx := rowIdx + 1), 1)
        
        # ? Configure layout row/column size(s).
        rowCount = rowIdx + 1
        for rowIdx in range(rowCount):
            self.rootLayout.setRowMinimumSize(rowIdx, 0)
        self.rootLayout.setColumnMinimumSize(1, 0)

# ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Construct GUI.

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

textEdit_ARXML = GElements.Widgets.Basics.TextEdit(isEditable=False, isMonospaced=True)
elementQueryWidget = ElementQueryWidget()

rootLayout = GElements.Layouts.GridLayout(2, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(textEdit_ARXML, 0, 0)
rootLayout.setWidget(elementQueryWidget, 1, 0)
rootLayout.setRowMinimumSize(1, 0)

window = GElements.Window(title=constants['title'],
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'])

# ? Run GUI loop.
window.show()
application.run()
