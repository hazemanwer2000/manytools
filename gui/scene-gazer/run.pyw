
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Resources as Resources
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.OS.Clipboard as Clipboard

import traceback
import sys
import typing
from pprint import pprint

class Utils:

    class Metadata:

        @staticmethod
        def parseTags(metadata:dict) -> typing.List[str]:
            
            tags = metadata['tags']

            # ? Check if all tag value(s) are string(s).
            if True != all([(type(tag) is str) for tag in tags]):
                raise ExceptionUtils.ValidationError("A non-string tag value was found.")
            
            return tags

    class Dialog:

        @staticmethod
        def reportError(msg:str):
            GElements.StandardDialog.showInformation('Error', msg, Constants.ErrorDialogSize, isSizeFixed=True)

    class CustomWidget:

        class TagsWidget(GElements.CustomWidget):

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

except Exception as e:

    Utils.Dialog.reportError(traceback.format_exc())
    exit(1)

# ? Construct GUI.

videoPlayer = GElements.Widgets.Complex.VideoPlayer()
videoPlayer.load(f_video)

tagsWidget = Utils.CustomWidget.TagsWidget(tags)

tabWidget = GElements.Widgets.Containers.TabContainer(
    tabNames=Constants.TabNames,
    widgets=[
        GElements.Widgets.Basics.Null(),
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
