
import automatey.GUI.GElements as GElements
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Resources as Resources
import automatey.Media.VideoUtils as VideoUtils
import automatey.Utils.StringUtils as StringUtils
import automatey.OS.ProcessUtils as ProcessUtils

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

            class Node(GElements.Widgets.Basics.Tree.Node):

                def __init__(self, pseudoNode:"Utils.CustomWidget.Tree.PseudoNode"):
                    
                    self.pseudoNode = pseudoNode
                    self.children = [Utils.CustomWidget.Tree.Node(x) for x in pseudoNode.getChildren()]

                    # ? Construct attribute(s).
                    attribute_name = pseudoNode.f_root.getNameWithoutExtension()
                    attribute_size = StringUtils.MakePretty.Size(pseudoNode.f_root.getSize()) if pseudoNode.f_root.isFile() else ''
                    extension = pseudoNode.f_root.getExtension()
                    attribute_extension = extension.upper() if (extension is not None) else ''
                    self.attributes = [attribute_name, attribute_extension, attribute_size, '■']

                def getChildren(self):
                    return self.children
            
                def getAttributes(self):
                    return self.attributes
                
            class PseudoNode:

                def __init__(self, f_root:FileUtils.File):
                    
                    self.f_root = f_root
                    self.children = []

                    if f_root.isDirectory():

                        f_list = f_root.listDirectory(conditional=lambda x: x.isDirectory() or VideoUtils.Video.Utils.isVideo(x))
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

class Constants:

    TreeColumnOffset = 20

    class Commands:

        OpenWith = {
            "default-handler" : ProcessUtils.CommandTemplate(
                r"start",
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

treeWidget = GElements.Widgets.Basics.Tree(
    rootNode=Utils.CustomWidget.Tree.Node(pseudoRootNode),
    header=Utils.CustomWidget.Tree.Headers
)
treeWidget.expandAll()
treeWidget.resizeColumnsToContents(Constants.TreeColumnOffset)

# ? ? Construct Root Layout.

rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(treeWidget, 0, 0)

# ? ? Window.

window = GElements.Window(title=constants['title'] + '  |  ' + str(f_root),
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'])

# ? ? Create Tree Context-Menu.

def openWith(commandKey):
    node = treeWidget.getContextInfo()
    f_selected = node.pseudoNode.f_root
    if f_selected.isFile():
        commandFormatter = Constants.Commands.OpenWith[commandKey].createFormatter()
        commandFormatter.assertParameter("file-path", str(f_selected))
        subprocess.Popen(str(commandFormatter), shell=True)

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

def treeContextMenuCallout():
    node = treeWidget.getContextInfo()
    f_selected = node.pseudoNode.f_root
    if f_selected.isFile():
        treeWidget.showContextMenu(fileContextMenu)

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
