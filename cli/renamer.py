
import sys
import traceback
from pprint import pprint

import automatey.OS.FileUtils as FileUtils
import automatey.Base.ExceptionUtils as ExceptionUtils
import automatey.Utils.Validation as Validation
import automatey.OS.Specific.Windows as Windows

fileConditional = {
    True : (lambda x: x.isFile()),
    False : (lambda x: True),
}

try:

    prefix = input('Prefix [Optional]: ').strip()
    suffix = input('Suffix [Optional]: ').strip()
    isFilesOnly = Validation.asBool(input('Process files only? (yes/no): ').strip())

    f_srcDir = FileUtils.File(sys.argv[1])
    f_fileList = f_srcDir.listDirectory(conditional=fileConditional[isFilesOnly])
    Windows.Utils.sort(f_fileList, lambda x: str(x))

    code = input("Do you really want to? [Say 'yesido']: ").strip()
    if code != 'yesido':
        raise ExceptionUtils.ValidationError("It seems you got ere' by mistake. No-problemo! No harm done.")

    digitCount = len(str(len(f_fileList)))
    for idx, f in enumerate(f_fileList):
        newName = prefix + str(idx + 1).zfill(digitCount) + suffix
        FileUtils.File.Utils.rename(f, newName)

except Exception as e:
    traceback.print_exc()
else:
    print('Renamed all file(s) successfully.')

input()