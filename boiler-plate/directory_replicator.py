
import automatey.OS.FileUtils as FileUtils

# ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ 
# Insert your code below (...)

path_dir = "..."

def conditional(f:FileUtils.File):
    return f.isFile()

def process(f_input:FileUtils.File, f_output:FileUtils.File):
    pass

# ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻

f_dir = FileUtils.File(path_dir)

f_dstDir = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_dir)))
f_dstDir.makeDirectory()

path_inputs = f_dir.listDirectoryRelatively(isRecursive=True, conditional=conditional)

f_inputs = []
f_outputs = []

FileUtils.File.Utils.replicateDirectoryStructure(f_dir, f_dstDir)

for path_input in path_inputs:
    f_input = f_dir.traverseDirectory(path_input)
    f_output = f_dstDir.traverseDirectory(path_input)
    process(f_input, f_output)
    
FileUtils.File.Utils.removeEmptySubDirectories(f_dstDir)
