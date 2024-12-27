
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON
import automatey.OS.Specific.Windows as Windows

# ? Get app's root directory.
f_appDir = FileUtils.File(__file__).traverseDirectory('..')

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

# ? Create Start-Menu shortcut.

Windows.Shortcut.toStartMenu(name=constants['start-menu']['name'],
                             f_icon=FileUtils.File(constants['start-menu']['icon-path']),
                             f_exe=f_appDir.traverseDirectory('run.pyw'))

print("Start menu shortcut created successfully.")
