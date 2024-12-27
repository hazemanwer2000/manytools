
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON

# ! Shared data.

f_cwd = FileUtils.File.Utils.getWorkingDirectory()

# ? Load settings.

f_settings = f_cwd.traverseDirectory('settings.json')
settings = JSON.fromFile(f_settings)

# ? Collect template file(s).

f_templates = f_cwd.listDirectory(isRecursive=True, conditional=(lambda f: f.getExtension() == 'ttt'))

# ? Process template file(s).

for f_template in f_templates:
    
    # ? Setup formatter.
    fileFormatter = ProcessUtils.FileTemplate.fromFile(f_template).createFormatter()
    
    # ? Format (...)
    
    # ? ? Parameter: CURRENT-DIRECTORY
    f_templateDir = f_template.traverseDirectory('..')
    f_templateDirAbs = f_cwd.traverseDirectory(str(f_templateDir))
    fileFormatter.assertParameter('current-directory', str(f_templateDirAbs))

    # ? ? Parameter: BASE-DIRECTORY
    fileFormatter.assertParameter('base-directory', str(f_cwd))
    
    # ? ? Replace 'global-macros'.
    global_macros = settings['global-macros']
    for macro_name in global_macros:
        fileFormatter.assertParameter(macro_name.lower(), global_macros[macro_name])
    
    # ? Write file instance.
    f_instance = FileUtils.File(FileUtils.File.Utils.Path.modifyName(str(f_template), extension=''))
    if f_instance.isExists():
        FileUtils.File.Utils.recycle(f_instance)
    fileFormatter.saveAs(f_instance)