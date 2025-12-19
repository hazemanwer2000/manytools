
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON

import jinja2

f_cwd = FileUtils.File.Utils.getWorkingDirectory()

# ? Load settings.
f_settings = f_cwd.traverseDirectory('settings.json')
settings = JSON.fromFile(f_settings)

# ? Collect template file(s).
f_templates = f_cwd.listDirectory(isRecursive=True, conditional=(lambda f: f.getExtension() == 'ttt'))

# ? Process template file(s).

for f_template in f_templates:

    templateDict = dict()
    
    # ? Read template.
    template = jinja2.Template(f_template.quickRead('t'))
    
    # ? ? Parameter: CURRENT-DIRECTORY
    f_templateDir = f_template.traverseDirectory('..')
    f_templateDirAbs = f_cwd.traverseDirectory(str(f_templateDir))
    templateDict['current_directory'] = str(f_templateDirAbs)

    # ? ? Parameter: BASE-DIRECTORY
    templateDict['base_directory'] = str(f_cwd)

    # ? ? Parameter(s): GLOBAL-MACROS
    global_macros = settings['global-macros']
    for macro_name in global_macros:
        templateDict[macro_name] = global_macros[macro_name]
    
    # ? Instantiate template, and save.
    f_instance = FileUtils.File(FileUtils.File.Utils.Path.modifyName(str(f_template), extension=''))
    if f_instance.isExists():
        FileUtils.File.Utils.recycle(f_instance)
    f_instance.quickWrite(template.render(**templateDict), 't')
