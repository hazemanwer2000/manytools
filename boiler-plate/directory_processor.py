
import automatey.OS.FileUtils as FileUtils

import os

# Optional (...)
def renameFiles(f_src:FileUtils.File, f_dst:FileUtils.File):
    os.rename(str(f_src), str(f_dst))

# ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ ︼ 
# Insert your code below (...)

path_dir = "..."

def conditional(f:FileUtils.File):
    return f.isFile()

def process(f_input:FileUtils.File):
    pass

# ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻ ︻

f_dir = FileUtils.File(path_dir)

f_inputs = f_dir.listDirectory(isRecursive=True, conditional=conditional)

for f_input in f_inputs:
    process(f_input)
