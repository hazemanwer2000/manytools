
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
import automatey.OS.Clipboard as Clipboard

import traceback
import sys
import typing
from pprint import pprint
import os
from collections import OrderedDict

class Utils:

    class Metadata:

        @staticmethod
        def parseTags(metadata:dict) -> typing.List[str]:
            '''
            Parses tag(s) from metadata.

            Returns `None` if not defined.
            '''
            
            result = None

            if 'tags' in metadata:
                
                result = OrderedDict()
                
                # ? Parse tag(s).
                for tag in metadata['tags']:                    
                    
                    tagCategory, tagLabel = tag.split('/')
                    tagLabel = tagLabel.strip()
                    
                    if tagCategory not in result:
                        result[tagCategory] = set()
                    
                    result[tagCategory].add(tagLabel)
                
                # ? Sort tag(s) alphabetically.
                # ? ? Sort tag categories.
                result = OrderedDict(sorted(result.items(), key=lambda x: x[0]))
                # ? ? Sort tag categories content.
                for key in result:
                    result[key] = list(result[key])
                    result[key].sort()

            return result
        
        @staticmethod
        def parseChapters(metadata:dict) -> typing.List[str]:
            
            chapters = []

            for rawChapter in metadata['chapters']:

                chapter = {}
                chapter['description'] = str(rawChapter['description'])
                chapter['timestamp'] = TimeUtils.Time.createFromString(rawChapter['timestamp'])

                chapters.append(chapter)

            chapters.sort(key=lambda chapter: chapter['timestamp'])

            for idx, chapter in enumerate(chapters):
                chapter['index'] = idx + 1
            
            return chapters
        
        @staticmethod
        def parseHighlights(metadata:dict) -> typing.List[str]:
            
            highlights = []

            for rawHighlight in metadata['highlights']:

                highlight = {}
                highlight['description'] = str(rawHighlight['description'])
                highlight['timestamp'] = TimeUtils.Time.createFromString(rawHighlight['timestamp'])

                highlights.append(highlight)
            
            return highlights

    class Dialog:

        @staticmethod
        def reportError(msg:str):
            GElements.StandardDialog.showInformation('Error', msg, Constants.ErrorDialogSize, isSizeFixed=True)

    class CustomWidget:

        class Chapter(GElements.CustomWidget):

            def __init__(self, entry:dict):

                # ? Setup GUI.

                self.rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
                super().__init__(GElements.Widgets.Decorators.Titled(self.rootWidget, str(entry['index']), isInnerOutline=True, isOuterOutline=True))

                self.rootLayout.setColumnMinimumSize(0, 0)
                self.rootLayout.setRowMinimumSize(0, 0)
                
                self.textEdit = GElements.Widgets.Basics.TextEdit(isWrapText=True, isEditable=False, isVerticalScrollBar=False, isHorizontalScrollBar=False, height=Constants.TextEditHeight)
                self.textEdit.setText(entry['description'])
                self.textEdit.setEventHandler(GUtils.EventHandlers.ClickEventHandler(self.INTERNAL_onSelect))

                self.colorBlock = GElements.Widgets.Basics.ColorBlock(Constants.Color_NoHighlight, (5, int(Constants.TextEditHeight * 0.667)))

                self.rootLayout.setWidget(self.colorBlock, 0, 0)
                self.rootLayout.setWidget(self.textEdit, 0, 1)

                # ? Setup other variable(s).

                self.videoRenderer = None

                self.timestamp = entry['timestamp']

            def attachvideoRenderer(self, videoRenderer:GElements.Widgets.Basics.VideoRenderer):
                self.videoRenderer = videoRenderer

            def highlight(self, flag:bool):
                color = Constants.Color_Highlight if flag else Constants.Color_NoHighlight
                self.colorBlock.setColor(color)

            def INTERNAL_onSelect(self):
                if (self.videoRenderer is not None):
                    self.videoRenderer.seekPosition(self.timestamp)

        class Chapters(GElements.CustomWidget):

            def __init__(self, entries:typing.List[dict]):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                self.instances:typing.List['Utils.CustomWidget.Chapter'] = []

                for entry in entries:
                    instance = Utils.CustomWidget.Chapter(entry)
                    self.instances.append(instance)
                    self.rootWidget.getLayout().insertWidget(instance)
            
            def getInstances(self) -> typing.List['Utils.CustomWidget.Chapter']:
                return self.instances
            
            def attachvideoRenderer(self, videoRenderer:GElements.Widgets.Basics.VideoRenderer):
                for instance in self.instances:
                    instance.attachvideoRenderer(videoRenderer)

        class Highlight(GElements.CustomWidget):

            def __init__(self, entry:dict, videoRenderer:GElements.Widgets.Basics.VideoRenderer):

                # ? Setup other variable(s).

                self.videoRenderer = videoRenderer

                self.timestamp = entry['timestamp']

                # ? Setup GUI.

                self.rootLayout = GElements.Layouts.GridLayout(2, 1, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
                super().__init__(GElements.Widgets.Decorators.Outline(self.rootWidget, elementMargin=AbstractGraphics.SymmetricMargin(5)))

                self.rootLayout.setRowMinimumSize(0, 0)
                self.rootLayout.setRowMinimumSize(1, 0)
                
                self.textEdit = GElements.Widgets.Basics.TextEdit(isWrapText=True, isEditable=False, isVerticalScrollBar=False, isHorizontalScrollBar=False, height=Constants.TextEditHeight)
                self.textEdit.setText(entry['description'])
                self.textEdit.setEventHandler(GUtils.EventHandlers.ClickEventHandler(self.INTERNAL_onSelect))

                sliderRangeFrom = [0, int(self.videoRenderer.getDuration())]
                sliderRangeTo = [0, 1000000]
                sliderInitValue = int(MathUtils.mapValue(int(self.timestamp), sliderRangeFrom, sliderRangeTo))
                self.slider = GElements.Widgets.Basics.Slider(sliderRangeTo, sliderInitValue)
                self.slider.setEditable(False)

                self.rootLayout.setWidget(GElements.Widgets.Decorators.Margin(self.textEdit, AbstractGraphics.Margin(10, 0, 0, 10)), 0, 0)
                self.rootLayout.setWidget(self.slider, 1, 0)

            def INTERNAL_onSelect(self):
                if (self.videoRenderer is not None):
                    self.videoRenderer.seekPosition(self.timestamp)

        class Highlights(GElements.CustomWidget):

            def __init__(self, entries:typing.List[dict], videoRenderer:GElements.Widgets.Basics.VideoRenderer):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                self.instances:typing.List['Utils.CustomWidget.Highlight'] = []

                for entry in entries:
                    instance = Utils.CustomWidget.Highlight(entry, videoRenderer)
                    self.instances.append(instance)
                    self.rootWidget.getLayout().insertWidget(instance)
            
            def getInstances(self) -> typing.List['Utils.CustomWidget.Highlight']:
                return self.instances

        class TagCategory(GElements.CustomWidget):

            def __init__(self, tagCategory:str, tagLabels:typing.List[str]):

                self.rootLayout = GElements.Layouts.FlowLayout(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                self.rootWidget = GElements.Widgets.Decorators.Titled(GElements.Widget.fromLayout(self.rootLayout), tagCategory, isInnerOutline=True, isOuterOutline=True)
                
                super().__init__(self.rootWidget)

                for tagLabel in tagLabels:
                    tagLabelWidget = GElements.Widgets.Basics.Button(tagLabel)
                    tagLabelWidget.setEventHandler(GUtils.EventHandlers.ClickEventHandler(lambda tagLabel=tagLabel: print(tagLabel)))
                    self.rootLayout.insertWidget(tagLabelWidget)

        class Tags(GElements.CustomWidget):
                
            def __init__(self, tags:typing.OrderedDict[str, list]):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                for tagCategory in tags:

                    tagCategoryWidget = Utils.CustomWidget.TagCategory(tagCategory, tags[tagCategory])
                    self.rootWidget.getLayout().insertWidget(tagCategoryWidget)

class Constants:

    TabWidth = 350

    MetadataDirectoryName = '.metadata'

    ErrorDialogSize = (1000, 400)

    TextEditHeight = 80

    Color_Highlight = ColorUtils.Color.fromHEX("#FFFFFF")
    Color_NoHighlight = ColorUtils.Color.fromHEX("#1E1E1E")

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
    highlights = Utils.Metadata.parseHighlights(metadata)

except Exception as e:

    Utils.Dialog.reportError(traceback.format_exc())
    exit(1)

# ? Construct GUI.

videoPlayer = GElements.Widgets.Complex.VideoPlayer()
videoPlayer.load(f_video)

# ? ? Wait until video is loaded.
while int(videoPlayer.getRenderer().getDuration()) == 0:
    pass

tabWidgets = []
tabNames = []

if tags is not None:
    tagsWidget = Utils.CustomWidget.Tags(tags)
    tabWidgets.append(tagsWidget)
    tabNames.append("Tags")

chaptersWidget = Utils.CustomWidget.Chapters(chapters)
chaptersWidget.attachvideoRenderer(videoPlayer.getRenderer())
tabWidgets.append(chaptersWidget)
tabNames.append("Chapters")

highlightsWidget = Utils.CustomWidget.Highlights(highlights, videoPlayer.getRenderer())
tabWidgets.append(highlightsWidget)
tabNames.append("Highlights")

tabWidget = GElements.Widgets.Containers.TabContainer(
    tabNames=tabNames,
    widgets=tabWidgets
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

previousChapterWidget:Utils.CustomWidget.Chapter = None

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

    # ? Highlight current chapter.

    global previousChapterWidget
    
    # ? ? Determine current chapter.
    currentChapterIdx = None
    for idx in range(len(chapters)-1, -1, -1):
        if videoPosition >= chapters[idx]['timestamp']:
            currentChapterIdx = idx
            break

    # ? ? Get corresponding chapter widget.
    currentChapterWidget:Utils.CustomWidget.Chapter = None
    if currentChapterIdx is not None:
        currentChapterWidget = chaptersWidget.getInstances()[currentChapterIdx]
    
    # ? ? Check if necessary to change highlighted chapter.
    if currentChapterWidget is not previousChapterWidget:
        
        if previousChapterWidget is not None:
            previousChapterWidget.highlight(False)

        if currentChapterWidget is not None:
            currentChapterWidget.highlight(True)

        previousChapterWidget = currentChapterWidget

timer = GConcurrency.Timer(performRecurrentActivities, TimeUtils.Time.createFromMilliseconds(50))
timer.start()

# ? Create Tool-Bar.

def reload():
    os.execv(sys.executable, [sys.executable] + sys.argv)

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Reload',
        fcn=reload,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-reload.png'))),
    ),
]))

# ? Run GUI loop.
window.show()
application.run()
