
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.OS.FileUtils as FileUtils

# ! Shared data.

f_cwd = FileUtils.File.Utils.getWorkingDirectory()

# ? Collect template file(s).

f_templates = FileUtils.File('.').listDirectory(isRecursive=True, conditional=(lambda f: f.getExtension() == 'template'))

# ? Process template file(s).

for f_template in f_templates:
    
    # ? Setup formatter.
    fileFormatter = ProcessUtils.FileTemplate.fromFile(f_template).createFormatter()
    
    # ? Format (...)
    
    # ? ? Parameter: CURRENT-DIRECTORY
    f_templateDir = f_template.traverseDirectory('..')
    f_templateDirAbs = f_cwd.traverseDirectory(str(f_templateDir))
    fileFormatter.assertParameter('current-directory', str(f_templateDirAbs))
    
    # ? Write file instance.
    f_instance = FileUtils.File(FileUtils.File.Utils.Path.modifyName(str(f_template), extension=''))
    if f_instance.isExists():
        FileUtils.File.Utils.recycle(f_instance)
    fileFormatter.saveAs(f_instance)
