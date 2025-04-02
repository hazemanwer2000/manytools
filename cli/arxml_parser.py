
import automatey.GUI.GElements as GElements
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Formats.JSON as JSON
import automatey.Formats.ARXML as ARXML
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.Resources as Resources
import automatey.Utils.StringUtils as StringUtils
import automatey.Utils.DataStructure as DataStructure
import automatey.Utils.CLI as CLI
import automatey.Utils.ColorUtils as ColorUtils
import automatey.OS.Clipboard as Clipboard

from pprint import pprint
import sys
import subprocess

# ? Initialize useful object(s).

# ? ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? ? Construct temporary file(s).
f_tmpXML = FileUtils.File.Utils.getTemporaryFile('xml', prefix=constants['title'] + '-')
f_tmpGeneric = FileUtils.File.Utils.getTemporaryFile('txt', prefix=constants['title'] + '-')
f_tmpFiles = [
    f_tmpXML,
    f_tmpGeneric
]

class Constants:
    
    XMLIndentation = constants['settings']['indent-spaces-count'] * ' '
    ElementSelectThreshold = constants['settings']['element-select-threshold']
    WindowTitle = constants['title-pretty']
    Extension2ExternalView = {
        'xml' : {
            'viewer' : constants['settings']['xml-viewer'],
            'f_tmp' : f_tmpXML,
        },
        '*' : {
            'viewer' : constants['settings']['default-viewer'],
            'f_tmp' : f_tmpGeneric,
        },
    }

# ? ? Initialize ARXML parser.
CLI.echo('Parsing file(s)\n')

arxmlParser = ARXML.Parser()
f_arxmls = [FileUtils.File(path) for path in sys.argv[1].split(',')]
for f_arxml in f_arxmls:
    arxmlParser.processFile(f_arxml)

# ? ? Optimization: Convert all element(s) to text, upon load up.
element2XMLText = {}
element2ModelText = {}
with CLI.ProgressBar.create(arxmlParser.getElements(), 'Processing element(s)') as iterator:
    for element in iterator:
        # ? ? ? Get XML text.
        element2XMLText[element] = element.getXML().toString(indent=Constants.XMLIndentation)
        # ? ? ? Get Model text.
        elementModel = element.getModel()
        if elementModel is None:
            text = f"#ERROR: No model found ({element.getType()})."
        else:
            text = str(elementModel)
        element2ModelText[element] = text

# ? ? Optimization: Construct summary (of elements) upon load up.
CLI.echo('Summarizing element(s)\n')
elementsSummary = arxmlParser.summarize()

class WorkingPage:

    IsRenderXML:bool = True
    ElementHistory = DataStructure.History(constants['settings']['element-select-threshold'])

# ? Construct GUI.

class CustomWidgets:

    class EditCaseSensitive(GElements.CustomWidget):
        
        def __init__(self, editWidget):
            self.rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
            self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
            super().__init__(self.rootWidget)
            
            self.button_CaseSensitive = GElements.Widgets.Basics.Button(icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-text.png'))),
                                                                        toolTip='Match Case',
                                                                        isCheckable=True)
            self.rootLayout.setWidget(editWidget, 0, 0)
            self.rootLayout.setWidget(self.button_CaseSensitive, 0, 1)
            self.rootLayout.setColumnMinimumSize(1, 0)
        
        def isMatchCase(self) -> bool:
            return self.button_CaseSensitive.isChecked()

    class ElementQuery(GElements.CustomWidget):
        
        def __init__(self):
            self.rootLayout = GElements.Layouts.GridLayout(4, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
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
            self.lineEdit_QueryContains = GElements.Widgets.Basics.LineEdit(placeholder=':Contains', isEditable=True, isMonospaced=True)
            self.lineEditCS_QueryContains = CustomWidgets.EditCaseSensitive(GElements.Widgets.Decorators.LineEditEraser(self.lineEdit_QueryContains))
            self.button_Query = GElements.Widgets.Basics.Button(text='Search')
            
            # ? Set layout widget(s).
            rowIdx = -1
            self.rootLayout.setWidget(GElements.Widgets.Decorators.LineEditEraser(self.lineEdit_QueryPath), (rowIdx := rowIdx + 1), 0, colSpan=2)
            self.rootLayout.setWidget(GElements.Widgets.Decorators.LineEditEraser(self.lineEdit_QueryType), (rowIdx := rowIdx + 1), 0, colSpan=2)
            self.rootLayout.setWidget(self.lineEditCS_QueryContains, (rowIdx := rowIdx + 1), 0, colSpan=2)
            self.rootLayout.setWidget(self.button_Query, (rowIdx := rowIdx + 1), 1)
            
            # ? Configure layout row/column size(s).
            rowCount = rowIdx + 1
            for rowIdx in range(rowCount):
                self.rootLayout.setRowMinimumSize(rowIdx, 0)
            self.rootLayout.setColumnMinimumSize(1, 0)
        
        def getQueryArgs(self):
            queryPath = self.lineEdit_QueryPath.getText()
            queryType = self.lineEdit_QueryType.getText()
            queryContains = (self.lineEdit_QueryContains.getText(), self.lineEditCS_QueryContains.isMatchCase())
            return (queryPath, queryType, queryContains)
        
        def setEventHandler(self, eventHandler:GUtils.EventHandler):
            if isinstance(eventHandler, GUtils.EventHandlers.ClickEventHandler):
                self.button_Query.setEventHandler(eventHandler)
            else:
                raise ExceptionUtils.ValidationErrorError('Unsupported event handler type.')

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

textEdit_ARXML = GElements.Widgets.Basics.TextEdit(isEditable=False, isMonospaced=True)
customWidget_elementQuery = CustomWidgets.ElementQuery()

rootLayout = GElements.Layouts.GridLayout(2, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(textEdit_ARXML, 0, 0)
rootLayout.setWidget(customWidget_elementQuery, 1, 0)
rootLayout.setRowMinimumSize(1, 0)

window = GElements.Window(title=Constants.WindowTitle,
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'])

# ? Event handler(s).

# ? Helper.
def element2text(element:ARXML.Element):
    
    if WorkingPage.IsRenderXML:
        text = element2XMLText[element]
    else:
        text = element2ModelText[element]
    
    return text

# ? Helper.
def renderCurrentElement():
    
    currentElementPath = None
    text = None
    currentElement = WorkingPage.ElementHistory.current()

    # ? Fetch text.
    if currentElement is not None:
        currentElementPath = currentElement.getPath()
        text = element2text(currentElement)

    # ? Setup text.
    windowTitleExtension = '' if (currentElementPath is None) else f" [{currentElementPath}]"
    text = '' if (text is None) else text

    # ? Render (...)
    textEdit_ARXML.setText(text)
    window.setTitle(f"{Constants.WindowTitle}{windowTitleExtension}")

def navigateToPreviousElement():
    if WorkingPage.ElementHistory.current() is None:
        GElements.StandardDialog.Message.Announce.Information("No previous element in history.")
    else:
        WorkingPage.ElementHistory.previous()
        renderCurrentElement()

def navigateToNextElement():
    if WorkingPage.ElementHistory.next() is None:
        GElements.StandardDialog.Message.Announce.Information("No next element in history.")
    else:
        renderCurrentElement()

def viewAsXML(flag:bool):
    WorkingPage.IsRenderXML = flag
    renderCurrentElement()

# ? Helper.
def openExternallyGeneric(text, extension:str):
    externalView = Constants.Extension2ExternalView[extension]
    externalView['f_tmp'].quickWrite(text, 't')
    cmdArgs = [externalView['viewer'], str(externalView['f_tmp'])]
    subprocess.Popen(cmdArgs,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)

def openExternally():
    if WorkingPage.ElementHistory.current() is None:
        GElements.StandardDialog.Message.Announce.Information("Currently, no element selected.")
    else:
        text = textEdit_ARXML.getText()
        extension = 'xml' if WorkingPage.IsRenderXML else '*'
        openExternallyGeneric(text, extension)

def viewElementSummary():
    openExternallyGeneric(elementsSummary, '*')

# ? Helper.
def executeQueryStringConditionalConstructor(queryString:str, isCaseSensitive:bool=True):
    
    # ? Remove all white-space characters.
    queryString = queryString.replace(' ', '')
    
    # ? If empty, match anything.
    if queryString == '':
        queryString = '*'
    
    # ? Handle case-sensitive option.
    if isCaseSensitive:
        textModifier = lambda text: text
    else:
        queryString = queryString.lower()
        textModifier = lambda text: text.lower()
    
    # ? Use regex if '*' is present.
    if '*' in queryString:
        queryString = '^' + queryString.replace('*', '.*') + '$'
        queryConditional = lambda text: len(StringUtils.Regex.findAll(queryString, textModifier(text))) > 0
    else:
        queryConditional = lambda text: queryString == textModifier(text)
    
    return queryConditional

# ? Helper.
def executeQueryContainsConditionalConstructor(queryContains:str, isCaseSensitive:bool):
    
    # ? Match all elements, if query is unspecified.
    if queryContains == '':
        queryConditional = lambda element: True
    else:
        # ? Handle case-sensitive option.
        if isCaseSensitive:
            textModifier = lambda text: text
        else:
            queryContains = queryContains.lower()
            textModifier = lambda text: text.lower()
        
        # ? Always use 'RegEx'.
        queryContains = queryContains.replace('*', '[^\n]*')
        queryConditional = lambda element: len(StringUtils.Regex.findAll(queryContains, textModifier(element2text(element)))) > 0
    
    return queryConditional

# ? Helper.
def executeQueryConditionalConstructor(queryPath:str, queryType:str, queryContains:tuple):
    pathConditional = executeQueryStringConditionalConstructor(queryPath, isCaseSensitive=('*' not in queryPath))
    typeConditional = executeQueryStringConditionalConstructor(queryType, isCaseSensitive=False)
    containsConditional = executeQueryContainsConditionalConstructor(queryContains[0], isCaseSensitive=queryContains[1])
    return lambda element: (pathConditional(element.getPath()) and typeConditional(element.getType()) and containsConditional(element))

def executeQuery():
    queryPath, queryType, queryContains = customWidget_elementQuery.getQueryArgs()
    queryConditional = executeQueryConditionalConstructor(queryPath, queryType, queryContains)
    elementsQueried = arxmlParser.getElements(conditional=queryConditional)
    
    selectedElement = None
    
    if len(elementsQueried) == 0:
        GElements.StandardDialog.Message.Announce.Information("No matching elements found.")
    elif len(elementsQueried) == 1:
        selectedElement = elementsQueried[0]
    elif len(elementsQueried) > Constants.ElementSelectThreshold:
        GElements.StandardDialog.Message.Announce.Information(f"Too many matching elements found ({len(elementsQueried)} > {Constants.ElementSelectThreshold}).")
    else:
        elementsQueried.sort(key=lambda element: (element.getType(), element.getPath()))
        elementsQueriedSummary = [str(element) for element in elementsQueried]
        selectedElementIdx = GElements.StandardDialog.selectFromList(f'Select from {len(elementsQueried)} elements', elementsQueriedSummary, constants['gui']['dialog']['min-size'])
        if selectedElementIdx != -1:
            selectedElement = elementsQueried[selectedElementIdx]
    
    if (selectedElement is not None) and (selectedElement is not WorkingPage.ElementHistory.current()):
        WorkingPage.ElementHistory.insert(selectedElement)
        renderCurrentElement()

def copyElementPath():

    currentElement = WorkingPage.ElementHistory.current()

    # ? Fetch text.
    if currentElement is None:
        GElements.StandardDialog.Message.Announce.Information("Currently, no element selected.")
    else:
        Clipboard.copy(currentElement.getPath())

# ? Setup event handler(s).

customWidget_elementQuery.setEventHandler(GUtils.EventHandlers.ClickEventHandler(executeQuery))

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
    GUtils.Menu.Separator(),
    GUtils.Menu.EndPoint(
        text='View as XML',
        fcn=viewAsXML,
        icon=GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['xml'])),
        isCheckable=True,
        isChecked=WorkingPage.IsRenderXML,
    ),
    GUtils.Menu.Separator(),
    GUtils.Menu.EndPoint(
        text='Copy Element Path',
        fcn=copyElementPath,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-clone.png'))),
    ),
    GUtils.Menu.Separator(),
    GUtils.Menu.EndPoint(
        text='Open Externally',
        fcn=openExternally,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-share.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='View Summary',
        fcn=viewElementSummary,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-info.png'))),
    ),
]))

# ? Run GUI loop.
window.show()
application.run()

# ? Clean-up.
for f_tmpFile in f_tmpFiles:
    if f_tmpFile.isExists():
        FileUtils.File.Utils.recycle(f_tmpFile)
