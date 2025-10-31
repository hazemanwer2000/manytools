
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Resources as Resources
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.Utils.ColorUtils as ColorUtils
import automatey.Utils.MathUtils as MathUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.Clipboard as Clipboard

import traceback
import sys
import typing
from pprint import pprint
import os
from collections import OrderedDict

import Shared

class Utils:

    class CustomWidget:

        class Tree:

            Headers = ['Name']

            class Node(GElements.Widgets.Basics.Tree.Node):

                def __init__(self, pseudoNode:"Utils.CustomWidget.Tree.PseudoNode"):
                    
                    self.pseudoNode = pseudoNode
                    self.children = [Utils.CustomWidget.Tree.Node(x) for x in pseudoNode.getChildren()]
                    self.attributes = [pseudoNode.f_root.getNameWithoutExtension()]

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
                    pass

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

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

# ? ? Construct Root Layout.

rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(treeWidget, 0, 0)

# ? ? Window.

window = GElements.Window(title=constants['title'] + '  |  ' + str(f_root),
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'],
                          isEnableStatusBar=True)

# ? Run GUI loop.
window.show()
application.run()
