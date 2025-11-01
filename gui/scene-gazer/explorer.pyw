
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

import traceback
import sys
import typing
from pprint import pprint
from collections import OrderedDict
import subprocess

import Shared

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Utils:

    class CustomWidget:

        class Tree:

            Headers = ['Name', 'Extension', 'Size', '']

            FilterColumnIdx = 3

            class Node(GElements.Widgets.Basics.Tree.Node):

                def __init__(self, pseudoNode:"Utils.CustomWidget.Tree.PseudoNode"):
                    
                    self.pseudoNode = pseudoNode
                    self.children = [Utils.CustomWidget.Tree.Node(x) for x in pseudoNode.getChildren()]

                    # ? Fetch tag(s) (metadata).
                    self.tags = None
                    self.description = None
                    self.metadata = Shared.Utils.Metadata.find(pseudoNode.f_root)
                    if self.metadata is not None:
                        self.tags = Shared.Utils.Metadata.parseTags(self.metadata)
                        self.description = Shared.Utils.Metadata.parseDescription(self.metadata)

                    # ? Construct attribute(s).
                    attribute_name = pseudoNode.f_root.getNameWithoutExtension()
                    attribute_size = StringUtils.MakePretty.Size(pseudoNode.f_root.getSize()) if pseudoNode.f_root.isFile() else ''
                    extension = pseudoNode.f_root.getExtension()
                    attribute_extension = extension.upper() if (extension is not None) else ''
                    attribute_filter = Constants.FilterOutText if (self.tags is not None) else Constants.FilterExcludedText
                    self.attributes = [attribute_name, attribute_extension, attribute_size, attribute_filter]

                def getChildren(self):
                    return self.children
            
                def getAttributes(self):
                    return self.attributes
                
                def getUnionizedTags(self):

                    unionizedTags = self.tags

                    for child in self.getChildren():
                        extraTags = child.getUnionizedTags()
                        if unionizedTags is None:
                            unionizedTags = extraTags
                        elif extraTags is not None:
                            unionizedTags = Shared.Utils.Metadata.unionizeTags(unionizedTags, extraTags)
                    
                    return unionizedTags
                
                def filter(self, filterTags:OrderedDict) -> dict:

                    if self.tags is not None:
                        if len(filterTags.keys()) == 0:
                            self.attributes[Utils.CustomWidget.Tree.FilterColumnIdx] = Constants.FilterOutText
                        else:

                            # ? Filter algorithm.
                            isSelected = True
                            for filterTagCategory in filterTags:
                                
                                if filterTagCategory not in self.tags:
                                    isSelected = False
                                    break
                                else:
                                    isAnyMatchingLabel = False
                                    for filterTagLabel in filterTags[filterTagCategory]:
                                        if filterTagLabel in self.tags[filterTagCategory]:
                                            isAnyMatchingLabel = True
                                            break
                                        
                                    if not isAnyMatchingLabel:
                                        isSelected = False
                                        break
                            
                            self.attributes[Utils.CustomWidget.Tree.FilterColumnIdx] = (Constants.FilterInText if isSelected else Constants.FilterOutText)

                    for subNode in self.children:
                        subNode.filter(filterTags)

            class PseudoNode:

                def __init__(self, f_root:FileUtils.File):
                    
                    self.f_root = f_root
                    self.children = []

                    if f_root.isDirectory():

                        f_list = f_root.listDirectory(conditional=lambda x: x.isDirectory() or VideoUtils.Video.Utils.isVideo(x))
                        Windows.Utils.sort(f_list, lambda x: x.getName())
                        for f in f_list:
                            self.children.append(Utils.CustomWidget.Tree.PseudoNode(f))

                def getChildren(self):
                    return self.children
                
                def prune(self):

                    idx = 0
                    while idx < len(self.children):
                        
                        child = self.children[idx]

                        child.prune()
                        
                        if child.f_root.isDirectory() and (len(child.children) == 0):
                            del self.children[idx]
                        else:
                            idx += 1

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

            def getSelectedTags(self) -> OrderedDict:
                
                result = OrderedDict()

                selectedTagLabels = []
                for idx, tagLabelWidget in enumerate(self.tagLabelWidgets):
                    if tagLabelWidget.isChecked():
                        selectedTagLabels.append(self.tagLabels[idx])
                
                if len(selectedTagLabels) > 0:
                    result[self.tagCategory] = selectedTagLabels

                return result

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

            def getSelectedTags(self) -> OrderedDict:
                result = OrderedDict()
                for tagCategoryWidget in self.tagCategoryWidgets:
                    result.update(tagCategoryWidget.getSelectedTags())
                return result

        class TagsContainer(GElements.CustomWidget):

            def __init__(self, tagsWidget:"Utils.CustomWidget.Tags", onFilter):

                self.rootLayout = GElements.Layouts.GridLayout(2, 1, AbstractGraphics.SymmetricMargin(0), 0)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)

                super().__init__(self.rootWidget)

                # ? Create control bar.
                self.controlLayout = GElements.Layouts.FlowLayout(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                self.controlWidget = GElements.Widget.fromLayout(self.controlLayout)
                # ? ? (...)
                self.filterButton = GElements.Widgets.Basics.Button(icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-filter.png'))))
                self.controlLayout.insertWidget(self.filterButton)
                # ? ? (...)
                self.clearButton = GElements.Widgets.Basics.Button(icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-remove.png'))))
                self.controlLayout.insertWidget(self.clearButton)

                self.rootLayout.setWidget(tagsWidget, 0, 0)
                self.rootLayout.setWidget(self.controlWidget, 1, 0)
                self.rootLayout.setRowMinimumSize(1, 0)

                # ? Set event handler(s).
                self.clearButton.setEventHandler(GUtils.EventHandlers.ClickEventHandler(tagsWidget.deselectAll))
                self.filterButton.setEventHandler(GUtils.EventHandlers.ClickEventHandler(onFilter))

class Constants:

    TreeColumnOffset = 20
    TabWidth = 350
    WindowSize = (1100, 600)
    DescriptionDialogSize = (350, 250)

    FilterInText = '■'
    FilterOutText = '⬚'
    FilterExcludedText = ''

    WindowTitleTemplate = ProcessUtils.FileTemplate(constants['title'] + r'  |  {{{TEXT}}}')

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

# ? Construct GUI.

# ? ? Construct Tree Widget.

pseudoRootNode=Utils.CustomWidget.Tree.PseudoNode(f_root)
pseudoRootNode.prune()

rootNode = Utils.CustomWidget.Tree.Node(pseudoRootNode)

treeWidget = GElements.Widgets.Basics.Tree(
    rootNode=rootNode,
    header=Utils.CustomWidget.Tree.Headers
)
treeWidget.expandAll()
treeWidget.resizeColumnsToContents(Constants.TreeColumnOffset)

# ? ? Construct Root Layout.

tabWidgets = []
tabNames = []

def onFilter():
    selectedTags = tagsWidget.getSelectedTags()
    rootNode.filter(selectedTags)
    treeWidget.refresh(rootNode, isRecursive=True)

# ? ? ? Construct Tags Widget.
unionizedTags = rootNode.getUnionizedTags()
if unionizedTags is not None:
    tagsWidget = Utils.CustomWidget.Tags(unionizedTags)
    tagsContainerWidget = Utils.CustomWidget.TagsContainer(tagsWidget, onFilter)
    tabWidgets.append(tagsContainerWidget)
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

windowTitleFormatter = Constants.WindowTitleTemplate.createFormatter()
windowTitleFormatter.assertParameter('text', str(f_root))
window = GElements.Window(title=str(windowTitleFormatter),
                          rootLayout=rootLayout,
                          minimumSize=Constants.WindowSize)

# ? ? Create Tree Context-Menu.

def openWith(commandKey):
    node = treeWidget.getContextInfo()
    f_selected = node.pseudoNode.f_root
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

windowTitleFormatter = Constants.WindowTitleTemplate.createFormatter()
windowTitleFormatter.assertParameter('text', 'Description')
descriptionDialog = GElements.Dialog(str(windowTitleFormatter), descriptionDialogLayout, minimumSize=Constants.DescriptionDialogSize, isSizeFixed=True)

def showDescription():
    node = treeWidget.getContextInfo()
    if node.description is not None:
        descriptionDialogTextEdit.setText(node.description)
        descriptionDialog.run()

fileContextMenu = GUtils.Menu([
    GUtils.Menu.EndPoint(
        text=f'Open with Default Handler',
        fcn=lambda: openWith("default-handler"),
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-external-link.png'))),
    ),
    GUtils.Menu.EndPoint(
        text=f'Open with {constants['title']}',
        fcn=lambda: openWith("this"),
        icon=GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app']))
    )
])

directoryContextMenu = GUtils.Menu([
    GUtils.Menu.EndPoint(
        text=f'Open with Default Handler',
        fcn=lambda: openWith("file-explorer"),
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-external-link.png'))),
    ),
    GUtils.Menu.EndPoint(
        text=f'Read Description',
        fcn=showDescription,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-description.png'))),
    )
])

def treeContextMenuCallout():
    node = treeWidget.getContextInfo()
    f_selected = node.pseudoNode.f_root
    if f_selected.isFile():
        treeWidget.showContextMenu(fileContextMenu)
    else:
        treeWidget.showContextMenu(directoryContextMenu)

treeWidget.setContextMenuCallout(treeContextMenuCallout)

# ? ? Create Tool-Bar.

def collapseAll():
    treeWidget.collapseAll()

def expandAll():
    treeWidget.expandAll()

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
    )
]))

# ? Run GUI loop.
window.show()
application.run()
