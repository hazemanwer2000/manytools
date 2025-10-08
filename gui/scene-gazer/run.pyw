
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
import automatey.OS.Clipboard as Clipboard

import traceback
import sys
import typing
from pprint import pprint

class Utils:

    class Metadata:

        @staticmethod
        def parseTags(metadata:dict) -> typing.List[str]:
            
            return [str(tag) for tag in metadata['tags']]
        
        @staticmethod
        def parseChapters(metadata:dict) -> typing.List[str]:
            
            chapters = []

            for idx, rawChapter in enumerate(metadata['chapters']):

                chapter = {}
                chapter['description'] = str(rawChapter['description'])
                chapter['timestamp'] = TimeUtils.Time.createFromString(rawChapter['timestamp'])
                chapter['index'] = idx + 1

                chapters.append(chapter)
            
            return chapters

    class Dialog:

        @staticmethod
        def reportError(msg:str):
            GElements.StandardDialog.showInformation('Error', msg, Constants.ErrorDialogSize, isSizeFixed=True)

    class CustomWidget:

        class DescriptiveTimestamp(GElements.CustomWidget):

            def __init__(self, entry:dict):

                # ? Setup GUI.

                self.rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
                super().__init__(GElements.Widgets.Decorators.Titled(self.rootWidget, str(entry['index']), isInnerOutline=True, isOuterOutline=True))

                self.rootLayout.setColumnMinimumSize(0, 0)
                self.rootLayout.setRowMinimumSize(0, 0)
                
                self.textEdit = GElements.Widgets.Basics.TextEdit(isWrapText=True, isEditable=False, isVerticalScrollBar=False, isHorizontalScrollBar=False)
                self.textEdit.setText(entry['description'])
                self.textEdit.setEventHandler(GUtils.EventHandlers.ClickEventHandler(lambda: print("h")))

                self.colorBlock = GElements.Widgets.Basics.ColorBlock(Constants.Color_NotSelected, (5, 80))

                self.rootLayout.setWidget(self.colorBlock, 0, 0)
                self.rootLayout.setWidget(self.textEdit, 0, 1)

                # ? Setup other variable(s).

                self.videoRenderer = None

                self.timestamp = entry['timestamp']

            def attachVideoPlayer(self, videoRenderer:GElements.Widgets.Basics.VideoRenderer):
                self.videoRenderer = videoRenderer

            def select(self):
                self.colorBlock.setColor(Constants.Color_Selected)

            def deselect(self):
                self.colorBlock.setColor(Constants.Color_NotSelected)

        class DescriptiveTimestamps(GElements.CustomWidget):

            def __init__(self, entries:typing.List[dict]):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                self.widgets = []

                for entry in entries:
                    widget = Utils.CustomWidget.DescriptiveTimestamp(entry)
                    self.widgets.append(widget)
                    self.rootWidget.getLayout().insertWidget(widget)

        class Tags(GElements.CustomWidget):

            def __init__(self, tags:typing.List[str]):

                self.rootLayout = GElements.Layouts.FlowLayout(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
                super().__init__(self.rootWidget)

                self.tagWidgets = []

                for tag in tags:
                    tagWidget = GElements.Widgets.Basics.Button(tag)
                    tagWidget.setEventHandler(GUtils.EventHandlers.ClickEventHandler(lambda tag=tag: Clipboard.copy(tag)))
                    self.tagWidgets.append(tagWidget)
                    self.rootLayout.insertWidget(tagWidget)

class Constants:

    TabNames = ['Chapters', 'Highlights', 'Tags']
    TabWidth = 350

    MetadataDirectoryName = '.metadata'

    ErrorDialogSize = (1000, 400)

    Color_Selected = ColorUtils.Color.fromHEX("#FFFFFF")
    Color_NotSelected = ColorUtils.Color.fromHEX("#1E1E1E")

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Get video path (i.e., mandatory (only) argument).
f_video = FileUtils.File(sys.argv[1])

# ? Create application instance.

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

# ? Parse (video) metadata.

try:
    f_metadata = f_video.traverseDirectory('..', Constants.MetadataDirectoryName, f_video.getNameWithoutExtension() + '.json')
    
    if not f_metadata.isExists():
        raise ExceptionUtils.ValidationError("Metadata file does not exist.")
    
    metadata = JSON.fromFile(f_metadata)

    tags = Utils.Metadata.parseTags(metadata)
    chapters = Utils.Metadata.parseChapters(metadata)

except Exception as e:

    Utils.Dialog.reportError(traceback.format_exc())
    exit(1)

# ? Construct GUI.

videoPlayer = GElements.Widgets.Complex.VideoPlayer()
videoPlayer.load(f_video)

tagsWidget = Utils.CustomWidget.Tags(tags)
chaptersWidget = Utils.CustomWidget.DescriptiveTimestamps(chapters)

tabWidget = GElements.Widgets.Containers.TabContainer(
    tabNames=Constants.TabNames,
    widgets=[
        chaptersWidget,
        GElements.Widgets.Basics.Null(),
        tagsWidget
    ]
)

rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(videoPlayer, 0, 0)
rootLayout.setWidget(tabWidget, 0, 1)
rootLayout.setColumnMinimumSize(1, Constants.TabWidth)

window = GElements.Window(title=constants['title'] + '  |  ' + str(f_video),
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'],
                          isEnableStatusBar=True)

# ? Setup event handler(s).

# ? ? Setup timer (i.e., for recurrent activities).

def performRecurrentActivities():
    videoPosition = videoPlayer.getRenderer().getPosition()
    videoMousePosition = videoPlayer.getRenderer().getMousePosition()
    videoDuration = videoPlayer.getRenderer().getDuration()
    videoVolume = videoPlayer.getRenderer().getVolume()
    
    statusText = ', '.join([
        str(videoPosition) + ' / ' + str(videoDuration),
        str(videoMousePosition),
        str(videoVolume) + '%',
    ])
    window.setStatus(statusText)

timer = GConcurrency.Timer(performRecurrentActivities, TimeUtils.Time.createFromMilliseconds(50))
timer.start()

# ? ? Construct window toolbar.

def reloadMetadata():
    pass

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Reload Metadata',
        fcn=reloadMetadata,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-reload.png'))),
    ),
]))

# ? Run GUI loop.
window.show()
application.run()
