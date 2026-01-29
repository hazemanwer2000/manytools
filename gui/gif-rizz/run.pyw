
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.Utils.TimeUtils as TimeUtils
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON

from pprint import pprint

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Construct GUI.

application = GElements.Application()
application.setIcon(GUtils.Icon.createFromFile(FileUtils.File(constants['path']['icon']['app'])))

GIFPlayer = GElements.Widgets.Complex.GIFPlayer()
GIFPlayer.getRenderer().load(FileUtils.File(constants['path']['gif']['default']))

rootLayout = GElements.Layouts.GridLayout(1, 1, elementMargin=AbstractGraphics.SymmetricMargin(5), elementSpacing=0)
rootLayout.setWidget(GElements.Widgets.Decorators.ScrollArea(GIFPlayer,
                                                             AbstractGraphics.SymmetricMargin(0),
                                                             isVerticalScrollBar=True,
                                                             isHorizontalScrollBar=True), 0, 0)

window = GElements.Window(title=constants['title'],
                          rootLayout=rootLayout,
                          minimumSize=constants['gui']['window']['min-size'],
                          isEnableStatusBar=True)

# ? Setup event handler(s).

# ? ? Construct window toolbar.

f_srcDir = FileUtils.File.Utils.getWorkingDirectory()

def loadFile():
    
    global f_srcDir
    
    f:FileUtils.File = GElements.StandardDialog.selectExistingFile(f_srcDir)
    if (f != None) and (f.getExtension() == 'gif'):
        GIFPlayer.getRenderer().load(f)
        window.setTitle(constants['title'] + '  |  ' + str(f))
        f_srcDir = f.traverseDirectory('..')

window.createToolbar(GUtils.Menu([
    GUtils.Menu.EndPoint(
        text='Generate',
        fcn=loadFile,
        icon=GUtils.Icon.createFromLibrary(GUtils.Icon.StandardIcon.FileOpen),
    ),
]))

# ? ? Setup timer (i.e., for recurrent activities).

def performRecurrentActivities():
    GIFMousePosition = GIFPlayer.getRenderer().getMousePosition()
    
    statusText = ', '.join([
        str(GIFMousePosition),
    ])
    window.setStatus(statusText)

timer = GConcurrency.Timer(performRecurrentActivities, TimeUtils.Time.createFromMilliseconds(50))
timer.start()

# ? Run GUI loop.
window.show()
application.run()
