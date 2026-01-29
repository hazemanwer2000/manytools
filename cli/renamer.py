
import sys
import traceback
from pprint import pprint

import automatey.OS.FileUtils as FileUtils
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.Utils.Validation as Validation
import automatey.OS.Specific.Windows as Windows
import automatey.Utils.CLI as CLI

conditionals = [
    {
        'conditional' : (lambda x: x.isFile()),
        'name' : 'Files'
    },
    {
        'conditional' : (lambda x: x.isDirectory()),
        'name' : 'Directories'
    }
]

try:

    prefix = CLI.Input.getString('Prefix [Optional]: ')
    suffix = CLI.Input.getString('Suffix [Optional]: ')
    requestedDigitCount = CLI.Input.Repeater(lambda: CLI.Input.getInt('Number of digits to use for numbering [0 for auto]: '))
    fileClass = CLI.Input.Repeater(lambda: CLI.Input.getOption('Process which class of files? [Select Option]', [x['name'] for x in conditionals]))

    f_srcDir = FileUtils.File(sys.argv[1])
    f_fileList = f_srcDir.listDirectory(conditional=conditionals[fileClass]['conditional'])
    Windows.Utils.sort(f_fileList, lambda x: str(x))

    code = input("Do you really want to? [Say 'yesido']: ").strip()
    if code != 'yesido':
        raise ExceptionUtils.ValidationError("It seems you got ere' by mistake. No-problemo! No harm done.")

    digitCount = len(str(len(f_fileList))) if requestedDigitCount == 0 else requestedDigitCount
    for idx, f in enumerate(f_fileList):
        newName = prefix + str(idx + 1).zfill(digitCount) + suffix
        FileUtils.File.Utils.rename(f, newName)

except Exception as e:
    traceback.print_exc()
else:
    print('Renamed all file(s) successfully.')

input()