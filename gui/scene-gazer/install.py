
import winreg

import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.OS.Specific.Windows as Windows

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Setup some constant(s).
f_pythonw = FileUtils.File(constants['global-macros']['pythonw'])

# ? Add registry-key for context-menu.

# ? ? For viewer.

command_name = constants['context-menu']['name']["viewer"]
command = ' '.join([
    Windows.Utils.File2Path(f_pythonw, isDoubleQuoted=True),
    Windows.Utils.File2Path(f_appDir.traverseDirectory(constants['runners']['viewer']), isDoubleQuoted=True),
    '"%1"'
])

Windows.Registry.ContextMenu.createCommand(name=command_name,
                                           command=command,
                                           f_icon=FileUtils.File(constants['context-menu']['icon-path']),
                                           fileCategory=Windows.Registry.ContextMenu.FileCategory.AllFiles)

# ? ? For explorer.

command_name = constants['context-menu']['name']["explorer"]
command = ' '.join([
    Windows.Utils.File2Path(f_pythonw, isDoubleQuoted=True),
    Windows.Utils.File2Path(f_appDir.traverseDirectory(constants['runners']['explorer']), isDoubleQuoted=True),
    '"%1"'
])

Windows.Registry.ContextMenu.createCommand(name=command_name,
                                           command=command,
                                           f_icon=FileUtils.File(constants['context-menu']['icon-path']),
                                           fileCategory=Windows.Registry.ContextMenu.FileCategory.AllDirectories)

Windows.Registry.ContextMenu.createCommand(name=command_name,
                                           command=command,
                                           f_icon=FileUtils.File(constants['context-menu']['icon-path']),
                                           fileCategory=Windows.Registry.ContextMenu.FileCategory.AllDirectoriesAsBackground)

print("Context menu entry added successfully.")
