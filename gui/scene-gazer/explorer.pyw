
import automatey.GUI.GElements as GElements
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Resources as Resources
import automatey.Media.VideoUtils as VideoUtils
import automatey.Utils.StringUtils as StringUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.OS.Specific.Windows as Windows
import automatey.Utils.ExceptionUtils as ExceptionUtils

import traceback
import sys
import typing
from pprint import pprint
from collections import OrderedDict
import subprocess
import os

import jinja2

import SharedUtils.Metadata as Metadata

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Utils:

    class Dialog:

        @staticmethod
        def reportError(msg:str):
            GElements.StandardDialog.showInformation('Error', msg, Constants.ErrorDialogSize, isSizeFixed=True)

    class DataStructure:

        class FileNode:
            '''
            Represents a file, and self-grows to represent the file hierarchy beneathe it.

            Notes:
            - `conditional` determines if a non-directory file is included in the hierarchy or not.
            '''

            def __init__(self, f_root:FileUtils.File, conditional:lambda f:True):
                
                self.f_root = f_root
                self.children = []

                if f_root.isDirectory():

                    f_list = f_root.listDirectory(conditional=lambda x: (x.isDirectory() or (x.isFile() and conditional(x))))
                    Windows.Utils.sort(f_list, lambda x: x.getName())
                    for f in f_list:
                        self.children.append(Utils.DataStructure.FileNode(f, conditional))

            def getChildren(self):
                '''
                Returns the list of child `FileNode`(s).
                '''
                return self.children
            
            def asFile(self) -> FileUtils.File:
                return self.f_root

            def prune(self):
                '''
                Removes all child `FileNode`(s) that represent directories that do not contain non-directory file(s).
                '''
                idx = 0
                while idx < len(self.children):
                    
                    child = self.children[idx]

                    child.prune()
                    
                    if child.f_root.isDirectory() and (len(child.children) == 0):
                        del self.children[idx]
                    else:
                        idx += 1

    class CustomWidget:

        class FileTree:

            AttributeDefinition = [
                {
                    'key' : 'name',
                    'display-name' : 'Name'
                },
                {
                    'key' : 'extension',
                    'display-name' : 'Extension'
                },
                {
                    'key' : 'size',
                    'display-name' : 'Size'
                },
                {
                    'key' : 'length',
                    'display-name' : 'Length'
                },
                {
                    'key' : 'resolution',
                    'display-name' : 'Resolution'
                },
                {
                    'key' : 'filter-state',
                    'display-name' : ''
                }
            ]

            @staticmethod
            def getHeaders() -> typing.List[str]:
                return [element['display-name'] for element in Utils.CustomWidget.FileTree.AttributeDefinition]

            @staticmethod
            def constructHierarchy(dFileNode:"Utils.DataStructure.FileNode") -> "Utils.CustomWidget.FileTree.FileNode":
                '''
                Constructs hierarchy of `FileNode`(s), and returns root.
                '''
                return Utils.CustomWidget.FileTree.FileNode.INTERNAL_fromDFileNode(dFileNode)
            
            class Utils:

                @staticmethod
                def getAllTags(rootFileNode:"Utils.CustomWidget.FileTree.FileNode", conditional=lambda n:True):
                    '''
                    Fetches all tag(s) in the file hierarchy.

                    Note(s):
                    - `conditional` determines if the tags of `RegularFileNode` are included or not. 
                    '''
                    tags = None

                    queue = [rootFileNode]
                    
                    while (len(queue) > 0):
                        currentFileNode = queue.pop(0)
                        if isinstance(currentFileNode, Utils.CustomWidget.FileTree.RegularFileNode):
                            if conditional(currentFileNode):
                                currentTags = currentFileNode.getTags()
                                if tags is None:
                                    tags = currentTags
                                elif currentTags is not None:
                                    tags = Metadata.Tags.unionizeTags(tags, currentTags)
                        elif isinstance(currentFileNode, Utils.CustomWidget.FileTree.DirectoryNode):
                            queue.extend(currentFileNode.getChildren())
                        else:
                            raise ExceptionUtils.ImplementationError("Instance is of an unexpected type.")
                    
                    return tags
                
                @staticmethod
                def updateFilterState(rootFileNode:"Utils.CustomWidget.FileTree.FileNode", referenceTags):
                    '''
                    Update filter state of each in the file hierarchy, based on the input `referenceTags`.
                    '''
                    filteredInCount = 0

                    queue = [rootFileNode]
                    
                    while (len(queue) > 0):
                        currentFileNode = queue.pop(0)
                        if isinstance(currentFileNode, Utils.CustomWidget.FileTree.RegularFileNode):
                            currentTags = currentFileNode.getTags()
                            if currentTags is not None:
                                if len(referenceTags) == 0:
                                    currentFileNode.updateFilterState(Constants.FilterOutText)
                                else:
                                    isSubsetOf = Metadata.Tags.isSubsetTags(currentTags, referenceTags)
                                    if isSubsetOf:
                                        currentFileNode.updateFilterState(Constants.FilterInText)
                                        filteredInCount += 1
                                    else:
                                        currentFileNode.updateFilterState(Constants.FilterOutText)
                        elif isinstance(currentFileNode, Utils.CustomWidget.FileTree.DirectoryNode):
                            queue.extend(currentFileNode.getChildren())
                        else:
                            raise ExceptionUtils.ImplementationError("Instance is of an unexpected type.")

                    return filteredInCount

                @staticmethod
                def getRegularFileCount(rootFileNode:"Utils.CustomWidget.FileTree.FileNode"):
                    '''
                    Counts number of regular file(s) in the file hierarchy.
                    '''
                    fileCount = 0

                    queue = [rootFileNode]
                    
                    while (len(queue) > 0):
                        currentFileNode = queue.pop(0)
                        if isinstance(currentFileNode, Utils.CustomWidget.FileTree.RegularFileNode):
                            fileCount += 1
                        elif isinstance(currentFileNode, Utils.CustomWidget.FileTree.DirectoryNode):
                            queue.extend(currentFileNode.getChildren())
                        else:
                            raise ExceptionUtils.ImplementationError("Instance is of an unexpected type.")

                    return fileCount

            class FileNode(GElements.Widgets.Basics.Tree.Node):

                @staticmethod
                def INTERNAL_fromDFileNode(dFileNode:"Utils.DataStructure.FileNode") -> "Utils.CustomWidget.FileTree.FileNode":
                    return Utils.CustomWidget.FileTree.DirectoryNode(dFileNode) if dFileNode.asFile().isDirectory() else Utils.CustomWidget.FileTree.RegularFileNode(dFileNode)

                def __init__(self, dFileNode:"Utils.DataStructure.FileNode"):
                    
                    self.dFileNode = dFileNode
                    self.children = []
                    for dChildFileNode in dFileNode.getChildren():
                        self.children.append(Utils.CustomWidget.FileTree.FileNode.INTERNAL_fromDFileNode(dChildFileNode))

                    self.attributeMap:dict = None

                def asFile(self) -> FileUtils.File:
                    return self.dFileNode.asFile()

                def getChildren(self):
                    return self.children
            
                def getAttributes(self):
                    return [self.attributeMap[element['key']] for element in Utils.CustomWidget.FileTree.AttributeDefinition]

            class DirectoryNode(FileNode):

                def __init__(self, dFileNode):
                    super().__init__(dFileNode)

                    # ? Fetch metadata.
                    try:
                        self.description = None
                        self.metadata = Metadata.find(dFileNode.asFile())
                        if self.metadata is not None:
                            self.description = Metadata.Description.parseDescription(self.metadata)
                    except:
                        raise ExceptionUtils.ValidationError(f"Error occurred while parsing metadata: '{str(dFileNode.asFile())}'")

                    # ? Construct attribute map.
                    self.attributeMap = {
                        'name' : dFileNode.asFile().getNameWithoutExtension(),
                        'size' : '',
                        'extension' : '',
                        'length' : '',
                        'resolution' : '',
                        'filter-state' : Constants.FilterExcludedText
                    }

                def getDescription(self):
                    return self.description

            class RegularFileNode(FileNode):

                def __init__(self, dFileNode):
                    super().__init__(dFileNode)

                    # ? Fetch metadata.
                    try:
                        self.tags = None
                        self.description = None
                        self.metadata = Metadata.find(dFileNode.asFile())
                        if self.metadata is not None:
                            self.tags = Metadata.Tags.parseTags(self.metadata)
                            self.description = Metadata.Description.parseDescription(self.metadata)
                    except:
                        raise ExceptionUtils.ValidationError(f"Error occurred while parsing metadata: '{str(dFileNode.asFile())}'")

                    # ? Fetch video info.
                    video = VideoUtils.Video(dFileNode.asFile())
                    videoDimensions = video.getDimensions()

                    # ? Construct attribute map.
                    extension = dFileNode.asFile().getExtension()
                    self.attributeMap = {
                        'name' : dFileNode.asFile().getNameWithoutExtension(),
                        'size' : StringUtils.MakePretty.Size(dFileNode.asFile().getSize()),
                        'extension' : extension.upper() if (extension is not None) else '',
                        'length' : str(video.getDuration()),
                        'resolution' : f"({videoDimensions[0]}, {videoDimensions[1]})",
                        'filter-state' : Constants.FilterExcludedText if (self.tags is None) else Constants.FilterOutText
                    }

                def getDescription(self) -> str:
                    return self.description
                
                def getTags(self):
                    return self.tags

                def updateFilterState(self, filterState:str):
                    self.attributeMap['filter-state'] = filterState

                def isSelected(self) -> bool:
                    return self.attributeMap['filter-state'] == Constants.FilterInText

        class TagCategory(GElements.CustomWidget):

            def __init__(self, tagCategory:str, tagLabels:typing.List[str]):

                self.rootLayout = GElements.Layouts.FlowLayout(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                self.rootWidget = GElements.Widgets.Decorators.Titled(GElements.Widget.fromLayout(self.rootLayout), tagCategory, isInnerOutline=True)
                
                super().__init__(self.rootWidget)

                self.tagCategory = tagCategory
                self.tagLabels = tagLabels

                self.tagLabelWidgets = []
                for tagLabel in tagLabels:
                    tagLabelWidget = GElements.Widgets.Basics.Button(tagLabel, isCheckable=True)
                    self.tagLabelWidgets.append(tagLabelWidget)
                    self.rootLayout.insertWidget(tagLabelWidget)

            def deselectAll(self):
                for tagLabelWidget in self.tagLabelWidgets:
                    tagLabelWidget.setChecked(False)

            def registerOnTagToggle(self, fcn):
                for tagLabelWidget in self.tagLabelWidgets:
                    tagLabelWidget.setEventHandler(GUtils.EventHandlers.ClickEventHandler(fcn))

            def getSelectedTags(self) -> OrderedDict:
                '''
                Warning: This part of the implementation must be compatible with `Metadata` implementation.
                '''
                
                result = OrderedDict()

                selectedTagLabels = []
                for idx, tagLabelWidget in enumerate(self.tagLabelWidgets):
                    if tagLabelWidget.isChecked():
                        selectedTagLabels.append(self.tagLabels[idx])
                
                if len(selectedTagLabels) > 0:
                    result[self.tagCategory] = selectedTagLabels

                return result

            def updateTagEnabledState(self, enabledTags):

                for idx, tagLabelWidget in enumerate(self.tagLabelWidgets):

                    enabledState = True
                    
                    if len(enabledTags.keys()) > 0:
                        if self.tagCategory not in enabledTags:
                            enabledState = False
                        elif self.tagLabels[idx] not in enabledTags[self.tagCategory]:
                            enabledState = False

                    tagLabelWidget.setEnabled(enabledState)

        class Tags(GElements.CustomWidget):
                
            def __init__(self, tags:typing.OrderedDict[str, list]):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                self.tagCategoryWidgets = []
                for tagCategory in tags:
                    tagCategoryWidget = Utils.CustomWidget.TagCategory(tagCategory, tags[tagCategory])
                    self.tagCategoryWidgets.append(tagCategoryWidget)
                    self.rootWidget.getLayout().insertWidget(tagCategoryWidget)

            def deselectAll(self):
                for tagCategoryWidget in self.tagCategoryWidgets:
                    tagCategoryWidget.deselectAll()
            
            def registerOnTagToggle(self, fcn):
                for tagCategoryWidget in self.tagCategoryWidgets:
                    tagCategoryWidget.registerOnTagToggle(fcn)

            def getSelectedTags(self) -> OrderedDict:
                result = OrderedDict()
                for tagCategoryWidget in self.tagCategoryWidgets:
                    result.update(tagCategoryWidget.getSelectedTags())
                return result
            
            def updateTagEnabledState(self, enabledTags):
                for tagCategoryWidget in self.tagCategoryWidgets:
                    tagCategoryWidget.updateTagEnabledState(enabledTags)

        class TagsManager(GElements.CustomWidget):

            def __init__(self, tagsWidget:"Utils.CustomWidget.Tags", onSelectedTagsChange):

                self.rootLayout = GElements.Layouts.GridLayout(2, 1, AbstractGraphics.SymmetricMargin(0), 0)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)

                super().__init__(self.rootWidget)

                # ? Create control bar.
                self.controlLayout = GElements.Layouts.FlowLayout(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                self.controlWidget = GElements.Widget.fromLayout(self.controlLayout)
                # ? ? (...)
                self.clearButton = GElements.Widgets.Basics.Button(icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-remove.png'))))
                self.controlLayout.insertWidget(self.clearButton)

                self.rootLayout.setWidget(tagsWidget, 0, 0)
                self.rootLayout.setWidget(self.controlWidget, 1, 0)
                self.rootLayout.setRowMinimumSize(1, 0)

                # ? Set event handler(s).
                self.clearButton.setEventHandler(GUtils.EventHandlers.ClickEventHandler(self.INTERNAL_onClear))
                tagsWidget.registerOnTagToggle(onSelectedTagsChange)

                # ? (...)
                self.tagsWidget = tagsWidget
                self.onSelectedTagsChange = onSelectedTagsChange

            def INTERNAL_onClear(self):
                self.tagsWidget.deselectAll()
                self.onSelectedTagsChange()

            def updateTagEnabledState(self, enabledTags):
                self.tagsWidget.updateTagEnabledState(enabledTags)

class Constants:

    TreeColumnOffset = 20
    TabWidth = 350
    WindowSize = (1100, 600)
    DescriptionDialogSize = (350, 250)

    ErrorDialogSize = (1000, 400)

    FilterInText = '■'
    FilterOutText = '⬚'
    FilterExcludedText = ''

    WindowTitleTemplate = jinja2.Template(constants['title'] + r'  |  {{ root_path }}')

    class Commands:

        OpenWith = {
            "default-handler" : ProcessUtils.CommandTemplate(
                r"start",
                r"{{{FILE-PATH}}}"
            ),
            "file-explorer" : ProcessUtils.CommandTemplate(
                r"explorer",
                r"{{{FILE-PATH}}}"
            ),
            "this" : ProcessUtils.CommandTemplate(
                f"{constants["global-macros"]["python"]}",
                str(f_appDir.traverseDirectory(constants["runners"]["viewer"])),
                r"{{{FILE-PATH}}}"
            )
        }

# ? Get root path (i.e., mandatory (only) argument).
f_root = FileUtils.File(sys.argv[1])

# ? Create application instance.

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

splashScreen = GElements.SplashScreen(GUtils.Image(FileUtils.File(constants['path']['image']['splash-screen'])))
splashScreen.render(application)

# ? Construct GUI.

# ? ? Construct Tree Widget.

rootDFileNode=Utils.DataStructure.FileNode(f_root, conditional=lambda f: VideoUtils.Video.Utils.isVideo(f))
rootDFileNode.prune()

try:

    rootFileNode = Utils.CustomWidget.FileTree.constructHierarchy(rootDFileNode)

except Exception as e:

    Utils.Dialog.reportError(traceback.format_exc())
    exit(1)

treeWidget = GElements.Widgets.Basics.Tree(
    rootNode=rootFileNode,
    header=Utils.CustomWidget.FileTree.getHeaders()
)
treeWidget.expandAll()
treeWidget.resizeColumnsToContents(Constants.TreeColumnOffset)

# ? ? Construct Root Layout.

tabWidgets = []
tabNames = []

def onSelectedTagsChange():

    # ? Query current selected tags, and update attributes of file hierarchy accordingly.
    selectedTags = tagsWidget.getSelectedTags()
    filteredInCount = Utils.CustomWidget.FileTree.Utils.updateFilterState(rootFileNode, selectedTags)
    treeWidget.refresh(rootFileNode, isRecursive=True)

    # ? Fetch all tags of all selected in the file hierarchy, and update the state of the tags accordingly.
    # ? ? Warning: This part of the implementation must be compatible with `Metadata` implementation.
    allTagsOfSelected = Utils.CustomWidget.FileTree.Utils.getAllTags(rootFileNode, conditional=lambda n: n.isSelected())
    if allTagsOfSelected is None:
        allTagsOfSelected = OrderedDict()
    tagsManagerWidget.updateTagEnabledState(allTagsOfSelected)

    # ? Update window status.
    updateWindowStatus(filteredInCount)

# ? ? ? Construct Tags Widget.
allTags = Utils.CustomWidget.FileTree.Utils.getAllTags(rootFileNode)
if allTags is not None:
    tagsWidget = Utils.CustomWidget.Tags(allTags)
    tagsManagerWidget = Utils.CustomWidget.TagsManager(tagsWidget, onSelectedTagsChange)
    tabWidgets.append(tagsManagerWidget)
    tabNames.append("Tags")

if len(tabWidgets) > 0:

    tabWidget = GElements.Widgets.Containers.TabContainer(
        tabNames=tabNames,
        widgets=tabWidgets
    )

    rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
    rootLayout.setWidget(treeWidget, 0, 0)
    rootLayout.setWidget(tabWidget, 0, 1)
    rootLayout.setColumnMinimumSize(1, Constants.TabWidth)

else:

    rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
    rootLayout.setWidget(treeWidget, 0, 0)

# ? ? Window.
window = GElements.Window(title=Constants.WindowTitleTemplate.render(root_path=str(f_root)),
                          rootLayout=rootLayout,
                          minimumSize=Constants.WindowSize,
                          isEnableStatusBar=True)

# ? ? Create Tree Context-Menu.

def openWith(commandKey):
    fileNode = treeWidget.getContextInfo()
    f_selected = fileNode.asFile()
    commandFormatter = Constants.Commands.OpenWith[commandKey].createFormatter()
    commandFormatter.assertParameter("file-path", str(f_selected))
    command = str(commandFormatter).replace('/', '\\')
    subprocess.Popen(command, shell=True)

# ? ? ? Create Description Dialog.

descriptionDialogTextEdit = GElements.Widgets.Basics.TextEdit(isEditable=False, 
                                                            isWrapText=True,
                                                            isHorizontalScrollBar=False)

descriptionDialogLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
descriptionDialogLayout.setWidget(descriptionDialogTextEdit, 0, 0)

descriptionDialog = GElements.Dialog(Constants.WindowTitleTemplate.render(text='Description'), descriptionDialogLayout, minimumSize=Constants.DescriptionDialogSize, isSizeFixed=True)

def showDescription():
    fileNode = treeWidget.getContextInfo()
    description = fileNode.getDescription()
    if description is not None:
        descriptionDialogTextEdit.setText(description)
        descriptionDialog.run()

# ? ? ? (...)

menuItem_OpenWithDefaultHandler = GUtils.Menu.EndPoint(
    text=f'Open with Default Handler',
    fcn=lambda: openWith("default-handler"),
    icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-external-link.png'))),
)

menuItem_OpenWithFileExplorer = GUtils.Menu.EndPoint(
    text=f'Open with Default Handler',
    fcn=lambda: openWith("file-explorer"),
    icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-external-link.png'))),
)

menuItem_OpenWithThis = GUtils.Menu.EndPoint(
    text=f'Open with {constants['title']}',
    fcn=lambda: openWith("this"),
    icon=GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app']))
)

menuItem_ReadDescription = GUtils.Menu.EndPoint(
    text=f'Read Description',
    fcn=showDescription,
    icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-description.png'))),
)

def treeContextMenuCallout():

    fileNode = treeWidget.getContextInfo()
    contextMenuItemList = []
    
    if isinstance(fileNode, Utils.CustomWidget.FileTree.RegularFileNode):
        contextMenuItemList.extend([
            menuItem_OpenWithDefaultHandler,
            menuItem_OpenWithThis
        ])
    elif isinstance(fileNode, Utils.CustomWidget.FileTree.DirectoryNode):
        contextMenuItemList.extend([
            menuItem_OpenWithFileExplorer
        ])
    
    if fileNode.getDescription() is not None:
        contextMenuItemList.extend([
            GUtils.Menu.Separator(),
            menuItem_ReadDescription
        ])
    
    treeWidget.showContextMenu(GUtils.Menu(contextMenuItemList))

treeWidget.setContextMenuCallout(treeContextMenuCallout)

# ? ? Create Tool-Bar.

def collapseAll():
    treeWidget.collapseAll()

def expandAll():
    treeWidget.expandAll()

def reload():
    os.execv(sys.executable, [sys.executable] + sys.argv)

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Collapse All',
        fcn=collapseAll,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-minus.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Expand All',
        fcn=expandAll,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-plus.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Reload',
        fcn=reload,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-reload.png'))),
    ),
]))

# ? ? Setup window status.

fileNodeCount = Utils.CustomWidget.FileTree.Utils.getRegularFileCount(rootFileNode)

def updateWindowStatus(selectedNodeCount:int):
    window.setStatus(f"[ {selectedNodeCount} / {fileNodeCount} ]")

updateWindowStatus(0)

# ? Run GUI loop.
window.show()
splashScreen.derender(window)
application.run()
