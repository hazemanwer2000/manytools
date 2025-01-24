
import click

import subprocess
import os
import shlex

import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Abstract.Graphics as Graphics
import automatey.Base.ColorUtils as ColorUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.Base.TimeUtils as TimeUtils
import automatey.Media.ImageUtils as ImageUtils
import automatey.Utils.MathUtils as MathUtils
import automatey.Utils.StringUtils as StringUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.Cryptography as Cryptography
import automatey.Utils.CLI as CLI
import automatey.OS.Specific.Windows as Windows

class Utils:
    
    Constants = {
        'tracker-file-name' : 'dirtrack.json',
        'tracker-directory-name' : '.dirtrack',
        'hash-algorithm' : Cryptography.Hash.Algorithms.SHA256,
        
        'cli' : {
            'text-color' : {
                'report-error' : Graphics.TextColor(
                    foreground=ColorUtils.Colors.RED,
                    background=ColorUtils.Colors.BLACK,
                ),
                'report-info' : Graphics.TextColor(
                    foreground=ColorUtils.Colors.BLUE,
                    background=ColorUtils.Colors.BLACK,
                ),
                'delta-category' : Graphics.TextColor(
                    foreground=ColorUtils.Colors.PURPLE,
                    background=ColorUtils.Colors.WHITE,
                ),
                'delta-file-path' : Graphics.TextColor(
                    foreground=ColorUtils.Colors.WHITE,
                    background=ColorUtils.Colors.PURPLE,
                ),
            }
        },
    }
    
    class Report:
        
        @staticmethod
        def Error(msg:str):
            CLI.echo(f'[ERROR]: {msg}\n', textColor=Utils.Constants['cli']['text-color']['report-error'])

        @staticmethod
        def Info(msg:str):
            CLI.echo(f'[INFO]: {msg}\n', textColor=Utils.Constants['cli']['text-color']['report-info'])
        
        @staticmethod
        def Delta(delta):
            for category in delta['files']:
                filePathList = delta['files'][category]
                if len(filePathList) != 0:
                    CLI.echo(category.capitalize() + ':\n', textColor=Utils.Constants['cli']['text-color']['delta-category'])
                    for filePath in filePathList:
                        CLI.echo('  ' + filePath + '\n', textColor=Utils.Constants['cli']['text-color']['delta-file-path'])

    @staticmethod
    def constructDirectoryState():
        
        f_cwd = FileUtils.File.Utils.getWorkingDirectory()
        
        # ? Get a list of all file(s).
        allFilePaths = f_cwd.listDirectoryRelatively(isRecursive=True, conditional=lambda x: x.isFile() and not ((Utils.Constants['tracker-directory-name'] + '/') in str(x)))
        allFiles = [FileUtils.File(x) for x in allFilePaths]
        
        # ? Construct state.
        state = {
            'metadata' : {
                'creation-timestamp' : str(TimeUtils.DateTime.createFromNow()),
            },
            'files' : {},
        }
        # ? ? Construct file information.
        progressBar = CLI.ProgressBar(len(allFiles), label='Hashing files')
        for idx in progressBar.getIterator():
            f = allFiles[idx]
            hashAsBytes = Cryptography.Hash.generate(Cryptography.Feeds.FileFeed(f), algorithm=Utils.Constants['hash-algorithm'])
            fileState = {
                'hash' : StringUtils.HexString.fromBytes(hashAsBytes),
                'size' : StringUtils.MakePretty.Size(f.getSize()),
            }
            state['files'][str(f)] = fileState
        progressBar.close()

        return state

    @staticmethod
    def constructDelta(fromState, toState):
        fromFilePaths = set(fromState['files'].keys())
        toFilePaths = set(toState['files'].keys())
        
        # ? Construct file-path difference(s).
        filePaths_MayBeModified = fromFilePaths & toFilePaths
        filePaths_Deleted = fromFilePaths - toFilePaths
        filePaths_Added = toFilePaths - fromFilePaths
        # ? ? Identify modified file(s).
        filePaths_Modified = []
        for filePath in filePaths_MayBeModified:
            if fromState['files'][filePath]['hash'] != toState['files'][filePath]['hash']:
                filePaths_Modified.append(filePath)
        
        # ? Construct delta structure.
        delta = {
            'metadata' : {
                'is-directory-modified' : None,
            },
            'files' : {
                'deleted' : sorted(list(filePaths_Deleted)),
                'added' :  sorted(list(filePaths_Added)),
                'modified' : sorted(list(filePaths_Modified)),
            },
        }
        # ? ? Ammend metadata.
        isDirectoryModified = (len(delta['files']['deleted']) > 0) or (len(delta['files']['added']) > 0) or (len(delta['files']['modified']) > 0)
        delta['metadata']['is-directory-modified' ] = isDirectoryModified
        
        return delta

    @staticmethod
    def getReferenceState():
        f_trackList = SharedObjects.F_DirTrack.listDirectory()
        f_trackList.sort(key=lambda x: str(x))
        f_trackLast = f_trackList[-1]
        return JSON.fromFile(f_trackLast)

class SharedObjects:
    
    F_CWD:FileUtils.File = None
    F_DirTrack:FileUtils.File = None

    @staticmethod
    def initialize():
        SharedObjects.F_CWD = FileUtils.File.Utils.getWorkingDirectory()
        SharedObjects.F_DirTrack = SharedObjects.F_CWD.traverseDirectory(Utils.Constants['tracker-directory-name'])

    @staticmethod
    def cleanUp():
        pass

class CommandHandler:

    class Commit:
        
        @staticmethod
        def run():
            
            # ? (...)
            isCommit = None
            
            # ? Determine if must commit, or not (...)
            if not SharedObjects.F_DirTrack.isExists():
                SharedObjects.F_DirTrack.makeDirectory()
                currentState = Utils.constructDirectoryState()
                isCommit = True
                Utils.Report.Info('First commit in current directory.')
            else:
                referenceState = Utils.getReferenceState()
                currentState = Utils.constructDirectoryState()
                delta = Utils.constructDelta(referenceState, currentState)
                isCommit = delta['metadata']['is-directory-modified']
                if isCommit:
                    Utils.Report.Delta(delta)
                else:
                    Utils.Report.Error('Nothing to commit, directory un-changed.')
                
            # ? Commit, if (...)
            if isCommit:
                f_trackBase = SharedObjects.F_DirTrack.traverseDirectory(Utils.Constants['tracker-file-name'])
                f_trackNew = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_trackBase)))
                JSON.saveAs(currentState, f_trackNew)
                
    class Delta:
        
        @staticmethod
        def run():

            if not SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Current directory has no commit(s).")
            else:
                referenceState = Utils.getReferenceState()
                currentState = Utils.constructDirectoryState()
                delta = Utils.constructDelta(referenceState, currentState)
                isCommit = delta['metadata']['is-directory-modified']
                if isCommit:
                    Utils.Report.Delta(delta)
                else:
                    Utils.Report.Info('There is no delta, directory un-changed.')

@click.group()
def cli():
    '''
    'DirTrack' is meant to track the file change(s) within a directory.
    '''
    pass

@cli.command()
def commit():
    '''
    Commit the current state of the directory.
    '''
    SharedObjects.initialize()
    CommandHandler.Commit.run()
    SharedObjects.cleanUp()
    
@cli.command()
def delta():
    '''
    Determine the delta between the last commit, and the current state of the directory.
    '''
    SharedObjects.initialize()
    CommandHandler.Delta.run()
    SharedObjects.cleanUp()

if __name__ == '__main__':
    cli()
