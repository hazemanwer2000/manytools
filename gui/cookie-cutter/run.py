
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.Base.TimeUtils as TimeUtils

import sys
import time

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

rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=5)
rootLayout.setWidget(videoPlayer, 0, 0)
rootLayout.setWidget(trimTimesTable, 1, 0)

window = GElements.Window(title=constants['title'],
                          rootLayout=rootLayout,
                          minimumSize=constants['window']['minimum-size'],
                          isEnableStatusBar=True)

# ? Setup event handler(s).

# ? ? Setup timer (i.e., for recurrent activities).

def performRecurrentActivities():
    videoPosition = videoPlayer.getRenderer().getPosition()
    videoMousePosition = videoPlayer.getRenderer().getMousePosition()
    videoDuration = videoPlayer.getRenderer().getDuration()
    
    statusText = ', '.join([
        str(videoPosition) + ' / ' + str(videoDuration),
        str(videoMousePosition)
    ])
    window.setStatus(statusText)

timer = GConcurrency.Timer(performRecurrentActivities, TimeUtils.Time.createFromMilliseconds(50))
timer.start()

# ? Run GUI loop.
window.show()
application.run()
