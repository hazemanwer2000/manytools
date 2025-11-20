
import click

import subprocess
import os
import shlex

import automatey.OS.FileUtils as FileUtils
import automatey.OS.Specific.Windows as Windows
import automatey.Abstract.Graphics as Graphics
import automatey.Utils.ColorUtils as ColorUtils
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Utils.StringUtils as StringUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.Cryptography as Cryptography
import automatey.Utils.CLI as CLI

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
    def isTrackable(f:FileUtils.File):
        return f.isFile() and all([not (chunk in str(f)) for chunk in [
            Utils.Constants['tracker-directory-name'] + '/',
            '.git/',
            '.gitignore'
        ]])

    @staticmethod
    def constructDirectoryState():
        
        f_cwd = FileUtils.File.Utils.getWorkingDirectory()
        
        # ? Get a list of all file(s).
        allFilePaths = f_cwd.listDirectoryRelatively(isRecursive=True, conditional=Utils.isTrackable)
        allFiles = [FileUtils.File(x) for x in allFilePaths]
        
        # ? Construct state.
        state = {
            'metadata' : {
                'creation-timestamp' : str(TimeUtils.DateTime.createFromNow()),
                'file-count' : len(allFiles),
                'total-size' : None,
            },
            'files' : {},
        }
        # ? ? Construct file information.
        totalSize = 0
        with CLI.ProgressBar.create(allFiles, label='Hashing files') as iteratorWrapper:
            for f in iteratorWrapper:
                hashAsBytes = Cryptography.Hash.generate(Cryptography.Feeds.FileFeed(f), algorithm=Utils.Constants['hash-algorithm'])
                fileSize = f.getSize()
                totalSize += fileSize
                fileState = {
                    'hash' : StringUtils.HexString.fromBytes(hashAsBytes),
                    'metadata' : {
                        'size' : StringUtils.MakePretty.Size(fileSize),
                    },
                }
                state['files'][str(f)] = fileState
        state['metadata']['total-size'] = StringUtils.MakePretty.Size(totalSize)

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
                'deleted' : Windows.Utils.sorted(list(filePaths_Deleted)),
                'added' :  Windows.Utils.sorted(list(filePaths_Added)),
                'modified' : Windows.Utils.sorted(list(filePaths_Modified)),
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
        def run(isReset:bool=False):
            
            # ? If must reset, then (...)
            if isReset:
                if SharedObjects.F_DirTrack.isExists():
                    FileUtils.File.Utils.recycle(SharedObjects.F_DirTrack)
            
            # ? Determine if must commit, or not (...)
            isCommit = None
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
@click.option('--reset', is_flag=True, default=False, help='Delete all previous tracking history.')
def commit(reset):
    '''
    Commit the current state of the directory.
    '''
    SharedObjects.initialize()
    CommandHandler.Commit.run(reset)
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
