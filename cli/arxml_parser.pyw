
import automatey.GUI.GElements as GElements
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Formats.ARXML as ARXML
import automatey.Base.ExceptionUtils as ExceptionUtils
import automatey.Resources as Resources
import automatey.Utils.StringUtils as StringUtils
import automatey.Utils.DataStructure as DataStructure

from pprint import pprint
import sys

# ? Initialize useful object(s).

# ? ? Initialize ARXML parser.
f_arxmls = [FileUtils.File(path) for path in sys.argv[1].split(',')]
arxmlParser = ARXML.Parser()
for f_arxml in f_arxmls:
    arxmlParser.processFile(f_arxml)

# ? ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Constants:
    
    XMLIndentation = constants['settings']['element-xml-indent-spaces'] * ' '
    ElementSelectThreshold = constants['settings']['element-select-threshold']

class WorkingPage:
    
    CurrentElement:ARXML.Element = None
    IsRenderXML:bool = True
    ElementHistory = DataStructure.History(constants['settings']['element-select-threshold'])

# ? Construct GUI.

class ElementQueryWidget(GElements.CustomWidget):
    
    def __init__(self):
        self.rootLayout = GElements.Layouts.GridLayout(3, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
        self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
        super().__init__(GElements.Widgets.Decorators.Titled(self.rootWidget, 
                                                             "Element-Query",
                                                             elementMargin=AbstractGraphics.SymmetricMargin(5),
                                                             elementSpacing=5,
                                                             isOuterOutline=True,
                                                             isInnerOutline=True))
        
        # ? Create (sub-)widget(s).
        self.lineEdit_QueryPath = GElements.Widgets.Basics.LineEdit(placeholder=':Path', isEditable=True, isMonospaced=True)
        self.lineEdit_QueryType = GElements.Widgets.Basics.LineEdit(placeholder=':Type', isEditable=True, isMonospaced=True)
        self.button_Query = GElements.Widgets.Basics.Button(text='Search')
        
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
    
    def getQueryArgs(self):
        queryPath = self.lineEdit_QueryPath.getText()
        queryType = self.lineEdit_QueryType.getText()
        return (queryPath, queryType)
    
    def setEventHandler(self, eventHandler:GUtils.EventHandler):
        if isinstance(eventHandler, GUtils.EventHandlers.ClickEventHandler):
            self.button_Query.setEventHandler(eventHandler)
        else:
            raise ExceptionUtils.ValidationErrorError('Unsupported event handler type.')

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

# ? Event handler(s).

# ? Helper.
def renderCurrentElement():
    if WorkingPage.CurrentElement is None:
        text = ''
    else:
        if WorkingPage.IsRenderXML:
            text = WorkingPage.CurrentElement.getXML().toString(indent=Constants.XMLIndentation)
        else:
            elementModel = WorkingPage.CurrentElement.getModel()
            if elementModel is None:
                text = f"#ERROR: No model found ({WorkingPage.CurrentElement.getType()})."
            else:
                text = str(elementModel)
        textEdit_ARXML.setText(text)

def navigateToPreviousElement():
    pass

def navigateToNextElement():
    pass

def viewAsXML(flag:bool):
    WorkingPage.IsRenderXML = flag
    renderCurrentElement()

def openExternally():
    pass

# ? Helper.
def executeQueryStringConditionalConstructor(queryString:str, isCaseSensitve:bool=True):
    
    # ? Remove all white-space characters.
    queryString = queryString.replace(' ', '')
    
    # ? ? If empty, match anything.
    if queryString == '':
        queryString = '*'
    
    if isCaseSensitve:
        textModifier = lambda text: text
    else:
        queryString = queryString.lower()
        textModifier = lambda text: text.lower()
    
    # ? ? Use regex if '*' is present.
    if '*' in queryString:
        queryString = '^' + queryString.replace('*', '.*') + '$'
        queryConditional = lambda text: len(StringUtils.Regex.findAll(queryString, textModifier(text))) > 0
    else:
        queryConditional = lambda text: queryString == textModifier(text)
    
    return queryConditional

# ? Helper.
def executeQueryConditionalConstructor(queryPath:str, queryType:str):
    pathConditional = executeQueryStringConditionalConstructor(queryPath, isCaseSensitve=('*' not in queryPath))
    typeConditional = executeQueryStringConditionalConstructor(queryType, isCaseSensitve=False)
    return lambda element: (pathConditional(element.getPath()) and typeConditional(element.getType()))

def executeQuery():
    queryPath, queryType = elementQueryWidget.getQueryArgs()
    queryConditional = executeQueryConditionalConstructor(queryPath, queryType)
    elementsQueried = arxmlParser.getElements(conditional=queryConditional)
    
    selectedElement = None
    
    if len(elementsQueried) == 0:
        GElements.StandardDialog.Message.Announce.Error("No matching elements found.")
    elif len(elementsQueried) == 1:
        selectedElement = elementsQueried[0]
    elif len(elementsQueried) > Constants.ElementSelectThreshold:
        GElements.StandardDialog.Message.Announce.Error(f"Too many matching elements found ({len(elementsQueried)} > {Constants.ElementSelectThreshold}).")
    else:
        elementsQueried.sort(key=lambda element: (element.getType(), element.getPath()))
        elementsQueriedSummary = [(element.getType() + ': ' + element.getPath()) for element in elementsQueried]
        selectedElementIdx = GElements.StandardDialog.selectFromList(f'Select from {len(elementsQueried)} elements', elementsQueriedSummary, constants['gui']['dialog']['min-size'])
        selectedElement = elementsQueried[selectedElementIdx]
    
    if (selectedElement is not None) and (selectedElement is not WorkingPage.CurrentElement):
        WorkingPage.ElementHistory.insert(selectedElement)
        WorkingPage.CurrentElement = selectedElement
        renderCurrentElement()

# ? Setup event handler(s).

elementQueryWidget.setEventHandler(GUtils.EventHandlers.ClickEventHandler(executeQuery))

# ? Setup toolbar.

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Previous Element',
        fcn=navigateToPreviousElement,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-arrow-left.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Next Element',
        fcn=navigateToNextElement,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-arrow-right.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='View as XML',
        fcn=viewAsXML,
        icon=GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['xml'])),
        isCheckable=True,
        isChecked=WorkingPage.IsRenderXML,
    ),
    GUtils.Menu.EndPoint(
        text='Open Externally',
        fcn=openExternally,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-share.png'))),
    ),
]))

# ? Run GUI loop.
window.show()
application.run()
