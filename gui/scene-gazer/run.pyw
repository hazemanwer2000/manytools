
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
from pprint import pprint

class Constants:

    TabNames = ['Chapters', 'Highlights', 'Tags']
    TabWidth = 350

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

tabWidget = GElements.Widgets.Containers.TabContainer(
    tabNames=Constants.TabNames,
    widgets=[
        GElements.Widgets.Basics.Null(),
        GElements.Widgets.Basics.Null(),
        GElements.Widgets.Basics.Null()
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
