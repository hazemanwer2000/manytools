
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.OS.Specific.Windows as Windows

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')
appName = f_appDir.getName()
f_app = f_appDir.traverseDirectory('..', appName + '.py')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Add registry-key for context-menu.

command_name = constants['context-menu']['name']
command = ' '.join([
    '"' + constants['global-macros']['pythonw'].replace('/', '\\') + '"',
    str(f_app).replace('/', '\\'),
    '"%1"'
])

Windows.Registry.ContextMenu.createCommand(name=command_name,
                                           command=command,
                                           f_icon=FileUtils.File(constants['context-menu']['icon-path']),
                                           fileCategory=Windows.Registry.ContextMenu.FileCategory.AllFiles)

print("Context menu entry added successfully.")