
import sys
import traceback

import automatey.OS.FileUtils as FileUtils
import automatey.Base.ExceptionUtils as ExceptionUtils
import automatey.OS.Specific.Windows as Windows

try:

    f_srcDir = FileUtils.File(sys.argv[1])
    f_fileList = f_srcDir.listDirectory()
    
    Windows.Utils.sort(f_fileList, lambda x: str(x))
    
    prefix = input('Prefix [Optional]: ').strip()
    suffix = input('Suffix [Optional]: ').strip()

    code = input("Do you really want to? [Say 'yesido']: ").strip()
    if code != 'yesido':
        raise ExceptionUtils.ValidationError("It seems you got ere' by mistake. No-problemo! No harm done.")

    digitCount = len(str(len(f_fileList)))
    for idx, f in enumerate(f_fileList):
        newName = prefix + str(idx).zfill(digitCount) + suffix
        FileUtils.File.Utils.rename(f, newName)

except Exception as e:
    traceback.print_exc()
else:
    print('Renamed all file(s) successfully.')

input()