
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

import SharedUtils.Metadata as Metadata

class Utils:

    class Dialog:

        @staticmethod
        def reportError(msg:str):
            GElements.StandardDialog.showInformation('Error', msg, Constants.ErrorDialogSize, isSizeFixed=True)

    class CustomWidget:

        class Chapter(GElements.CustomWidget):

            def __init__(self, entry:dict, videoRenderer:GElements.Widgets.Basics.VideoRenderer):

                # ? Setup GUI.

                self.rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
                self.rootWidget = GElements.Widget.fromLayout(self.rootLayout)
                super().__init__(GElements.Widgets.Decorators.Titled(self.rootWidget, str(entry['index']), isInnerOutline=True, isOuterOutline=False))

                self.rootLayout.setColumnMinimumSize(0, 0)
                self.rootLayout.setRowMinimumSize(0, 0)
                
                self.textEdit = GElements.Widgets.Basics.TextEdit(isWrapText=True, isEditable=False, isTextSelectable=False, isVerticalScrollBar=False, isHorizontalScrollBar=False, height=Constants.TextEditHeight)
                self.textEdit.setText(entry['description'])
                self.textEdit.setEventHandler(GUtils.EventHandlers.ClickEventHandler(self.INTERNAL_onSelect))

                self.colorBlock = GElements.Widgets.Basics.ColorBlock(Constants.Color_NoHighlight, (5, int(Constants.TextEditHeight * 0.667)))

                self.rootLayout.setWidget(self.colorBlock, 0, 0)
                self.rootLayout.setWidget(self.textEdit, 0, 1)

                # ? Setup other variable(s).

                self.videoRenderer = videoRenderer

                self.timestamp = entry['timestamp']

            def highlight(self, flag:bool):
                color = Constants.Color_Highlight if flag else Constants.Color_NoHighlight
                self.colorBlock.setColor(color)

            def INTERNAL_onSelect(self):
                if (self.videoRenderer is not None):
                    self.videoRenderer.seekPosition(self.timestamp)

        class Chapters(GElements.CustomWidget):

            def __init__(self, entries:typing.List[dict], videoRenderer:GElements.Widgets.Basics.VideoRenderer):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                self.instances:typing.List['Utils.CustomWidget.Chapter'] = []

                for entry in entries:
                    instance = Utils.CustomWidget.Chapter(entry, videoRenderer)
                    self.instances.append(instance)
                    self.rootWidget.getLayout().insertWidget(instance)
            
            def getInstances(self) -> typing.List['Utils.CustomWidget.Chapter']:
                return self.instances

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
                
                self.textEdit = GElements.Widgets.Basics.TextEdit(isWrapText=True, isEditable=False, isTextSelectable=False, isVerticalScrollBar=False, isHorizontalScrollBar=False, height=Constants.TextEditHeight)
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
                self.rootWidget = GElements.Widgets.Decorators.Titled(GElements.Widget.fromLayout(self.rootLayout), tagCategory, isInnerOutline=True)
                
                super().__init__(self.rootWidget)

                for tagLabel in tagLabels:
                    tagLabelWidget = GElements.Widgets.Basics.Button(tagLabel)
                    tagLabelWidget.setEventHandler(GUtils.EventHandlers.ClickEventHandler(lambda tagLabel=tagLabel: Clipboard.copy(tagLabel)))
                    self.rootLayout.insertWidget(tagLabelWidget)

        class Tags(GElements.CustomWidget):
                
            def __init__(self, tags:typing.OrderedDict[str, list]):

                self.rootWidget = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
                super().__init__(GElements.Widgets.Decorators.ScrollArea(self.rootWidget, AbstractGraphics.SymmetricMargin(0), isVerticalScrollBar=True))

                for tagCategory in tags:

                    tagCategoryWidget = Utils.CustomWidget.TagCategory(tagCategory, tags[tagCategory])
                    self.rootWidget.getLayout().insertWidget(tagCategoryWidget)

        class Description(GElements.CustomWidget):

            def __init__(self, description:str):

                self.textEditWidget = GElements.Widgets.Basics.TextEdit(isEditable=False,
                                                                        isTextSelectable=False,
                                                                        isWrapText=True,
                                                                        isHorizontalScrollBar=False)
                self.textEditWidget.setText(description)    
        
                super().__init__(self.textEditWidget)

class Constants:

    TabWidth = 350

    ErrorDialogSize = (1000, 400)

    WindowSize = (1000, 600)

    TextEditHeight = 50

    Color_Highlight = ColorUtils.Color.fromHEX("#1E1E1E")
    Color_NoHighlight = ColorUtils.Color.fromHEX("#FFFFFF")

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

description = None
tags = None
chapters = None
highlights = None

try:

    metadata = Metadata.find(f_video)

    if metadata is not None:

        description = Metadata.Description.parseDescription(metadata)
        tags = Metadata.Tags.parseTags(metadata)
        chapters = Metadata.Chapters.parseChapters(metadata)
        highlights = Metadata.Highlights.parseHighlights(metadata)
        
        if (chapters is not None) and (highlights is not None):
            Metadata.Highlights.ammendHighlights(highlights, chapters)

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

if description is not None:
    descriptionWidget = Utils.CustomWidget.Description(description)
    tabWidgets.append(descriptionWidget)
    tabNames.append("Description")

if chapters is not None:
    chaptersWidget = Utils.CustomWidget.Chapters(chapters, videoPlayer.getRenderer())
    tabWidgets.append(chaptersWidget)
    tabNames.append("Chapters")

if highlights is not None:
    highlightsWidget = Utils.CustomWidget.Highlights(highlights, videoPlayer.getRenderer())
    tabWidgets.append(highlightsWidget)
    tabNames.append("Highlights")

if tags is not None:
    tagsWidget = Utils.CustomWidget.Tags(tags)
    tabWidgets.append(tagsWidget)
    tabNames.append("Tags")

if len(tabWidgets) > 0:

    tabWidget = GElements.Widgets.Containers.TabContainer(
        tabNames=tabNames,
        widgets=tabWidgets
    )

    rootLayout = GElements.Layouts.GridLayout(1, 2, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
    rootLayout.setWidget(videoPlayer, 0, 0)
    rootLayout.setWidget(tabWidget, 0, 1)
    rootLayout.setColumnMinimumSize(1, Constants.TabWidth)

else:

    rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
    rootLayout.setWidget(videoPlayer, 0, 0)

window = GElements.Window(title=constants['title'] + '  |  ' + str(f_video),
                          rootLayout=rootLayout,
                          minimumSize=Constants.WindowSize,
                          isEnableStatusBar=True)

# ? Setup timer (i.e., for recurrent activities).

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

    if chapters is not None:

        global previousChapterWidget
        
        # ? ? Determine current chapter.
        currentChapterIdx = Metadata.Chapters.findChapter(chapters, videoPosition)['index'] - 1

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
