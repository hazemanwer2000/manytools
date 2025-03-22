
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Utils.PyUtils as PyUtils
import automatey.Resources as Resources
import automatey.Utils.MathUtils as MathUtils

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

rootLayout = GElements.Layouts.GridLayout(2, 2, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(videoPlayer, 0, 0)
rootLayout.setWidget(trimTimesTable, 1, 0)
rootLayout.setWidget(filterList, 0, 1, rowSpan=2)
rootLayout.setRowMinimumSize(1, 0)
rootLayout.setColumnMinimumSize(1, 250)

window = GElements.Window(title=constants['title'] + '  |  ' + str(f_video),
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'],
                          isEnableStatusBar=True)

# ? ? App-wide announcement(s).
class Announcement:
    
    @staticmethod
    def VideoInformationStillLoading():
        GElements.StandardDialog.Message.Announce.Information('Video information is still being loaded.')

    @staticmethod
    def NoMoreKeyframes():
        GElements.StandardDialog.Message.Announce.Information('Video has no more keyframes.')

    @staticmethod
    def VideoGenerationSuccessful():
        GElements.StandardDialog.Message.Announce.Information('Video was generated successfully.')

    @staticmethod
    def VideoGenerationFailed():
        GElements.StandardDialog.Message.Announce.Error('Failed to generate video.')

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
    
    # ? ? ? Get time from table (as string).
    contextInfo = trimTimesTable.getContextInfo()
    timeFromTableAsString = trimTimesTable.getCell(contextInfo['row-index'], contextInfo['column-index'])
    
    # ? ? ? Attempt time conversion (from string).
    try:
        seekTime = TimeUtils.Time.createFromString(timeFromTableAsString)
    except:
        seekTime = None
    
    # ? ? ? If successful, seek time, else 
    if not (seekTime is None):
        videoPlayer.seekPosition(seekTime)

trimTimesTable.setContextMenu(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Seek',
        fcn=seekTimeFromTable,
    )
]))

# ? ? Construct processor thread.

def onVideoGenerationResult(result):
    GElements.StandardDialog.BackgroundActivity.release()
    if result['Status'] == 0:
        Announcement.VideoGenerationSuccessful()
    else:
        Announcement.VideoGenerationFailed()
        GElements.StandardDialog.showInformation('(...)', result['Info'], (1000, 400), isSizeFixed=True)
        
commandNotificationHandlers = {
    'Generate' : onVideoGenerationResult
}

def processorNotificationHandler(result:dict):
    commandNotificationHandlers[result['Command']](result['Result'])

Utils.Processor.initialize(f_video, FileUtils.File(constants['path']['template']['video-info']))
processorThread = GConcurrency.Thread(mainFcn=Utils.Processor.loop, notifyFcn=processorNotificationHandler)
processorThread.run()

# ? ? Construct window toolbar.

def jumpToNearestKeyframe(isForward:bool):
    if (not videoPlayer.getRenderer().isPlaying()):
        if Utils.Processor.VideoInformation.isInitialized == True:
            currentVideoPosition = videoPlayer.getRenderer().getPosition()
            # Fix: Because micro-seconds are neglected by the video-player, must increment by 1-ms when searching using current video position.
            if isForward:
                currentVideoPosition = currentVideoPosition + TimeUtils.Time.createFromMilliseconds(1)
            nearestValues = MathUtils.findNearestValues(currentVideoPosition, Utils.Processor.VideoInformation.keyframes)
            newVideoPosition = nearestValues[1] if isForward else nearestValues[0]
            if not (newVideoPosition is None):
                videoPlayer.seekPosition(newVideoPosition)
            else:
                Announcement.NoMoreKeyframes()
        else:
            Announcement.VideoInformationStillLoading()

def initiateVideoGeneration():
    
    GElements.StandardDialog.BackgroundActivity.awaitActivity()
    
    # ? Pause video first.
    videoPlayer.pause()
    
    commandStruct = {
        'Command' : 'Generate',
        'Arguments' : {
            'Trim-Times' : trimTimesTable.getEntries(),
            'Options' : filterList.getData(),
        },
    }
    Utils.Processor.commandQueue.enqueue(commandStruct)

def showVideoInformation():
    if Utils.Processor.VideoInformation.isInitialized == True:
        GElements.StandardDialog.showInformation('Video Information', Utils.Processor.VideoInformation.summary, (400, 125), isSizeFixed=True)
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
