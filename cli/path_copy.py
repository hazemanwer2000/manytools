
import sys

import automatey.OS.Clipboard as Clipboard

Clipboard.copy('"' + sys.argv[1].replace('\\', '/') + '"')
