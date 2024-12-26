
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Base.TimeUtils as TimeUtils
import automatey.Utils.PyUtils as PyUtils
import automatey.Resources as Resources

import sys
import time
from pprint import pprint

import Utils.CustomWidgets
import Utils.Processor

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Get video path (i.e., mandatory (only) argument).
f_video = FileUtils.File(sys.argv[1])

# ? Construct GUI.

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

videoPlayer = GElements.Widgets.Complex.VideoPlayer()
videoPlayer.load(f_video)

trimTimesTable = GElements.Widgets.Basics.EntryTable(['Start-Time', 'End-Time'])

filterOptionClassList = [attr for attr in Utils.CustomWidgets.FilterOptions.__dict__.values()
                         if (PyUtils.isClass(attr) and issubclass(attr, GElements.Widgets.Complex.FilterList.FilterOption))]
filterList = GElements.Widgets.Complex.FilterList(filterOptionClassList)

rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(videoPlayer, 0, 0)
rootLayout.setWidget(trimTimesTable, 1, 0)
rootLayout.setWidget(filterList, 0, 1, rowSpan=2)
rootLayout.setRowMinimumSize(1, 0)
rootLayout.setColumnMinimumSize(1, 250)

window = GElements.Window(title=constants['title'],
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'],
                          isEnableStatusBar=True)

# ? ? App-wide announcement(s).
class Announcement:
    
    @staticmethod
    def VideoInformationStillLoading():
        GElements.StandardDialog.Message.Announce.Warning('Video information is still being loaded.')

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

# ? ? Setup context-menu for 'Trim-Times-Table'.

def seekTimeFromTable():
    contextInfo = trimTimesTable.getContextInfo()
    timeFromTableAsString = trimTimesTable.getCell(contextInfo['row-index'], contextInfo['column-index'])
    seekTime = TimeUtils.Time.createFromString(timeFromTableAsString)
    videoPlayer.seekPosition(seekTime)

trimTimesTable.setContextMenu(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Seek',
        fcn=seekTimeFromTable,
    )
]))

# ? ? Construct processor thread.

def processorNotificationHandler(data:dict):
    print(data)

Utils.Processor.initialize(f_video)
processorThread = GConcurrency.Thread(mainFcn=Utils.Processor.loop, notifyFcn=processorNotificationHandler)
processorThread.run()

# ? ? Construct window toolbar.

def jumpToNearestKeyframe(isForward:bool):
    if Utils.Processor.VideoInformation.isInitialized == True:
        pass
    else:
        Announcement.VideoInformationStillLoading()

def initiateVideoGeneration():
    pass

def showVideoInformation():
    if Utils.Processor.VideoInformation.isInitialized == True:
        pass
    else:
        Announcement.VideoInformationStillLoading()

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Generate',
        fcn=initiateVideoGeneration,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-movie.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Previous Keyframe',
        fcn=lambda: jumpToNearestKeyframe(isForward=False),
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-hand-point-left.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Next Keyframe',
        fcn=lambda: jumpToNearestKeyframe(isForward=True),
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-hand-point-right.png'))),
    ),
    GUtils.Menu.EndPoint(
        text='Info',
        fcn=showVideoInformation,
        icon=GUtils.Icon.createFromFile(Resources.resolve(FileUtils.File('icon/lib/coreui/cil-info.png'))),
    ),
]))

# ? Run GUI loop.
window.show()
application.run()
