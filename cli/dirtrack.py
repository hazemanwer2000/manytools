
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

APP_NAME = 'dirtrack'

class Utils:
    
    Constants = {
        'iterator-length' : 6,
        'tracker-file-name' : f"{APP_NAME}.json",
        'tracker-directory-name' : f'.{APP_NAME}',
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
        'default-settings' : {
            'mode' : 'slow',
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
    def generateHashFromFile(f:FileUtils.File):
        if SharedObjects.Settings['mode'] == 'slow':
            hash = Cryptography.Hash.generate(Cryptography.Feeds.FileFeed(f), algorithm=Utils.Constants['hash-algorithm'])
        else:
            bytesToHash = str(f.getSize()).encode('utf-8')
            hash = Cryptography.Hash.generate(Cryptography.Feeds.BytesFeed(bytesToHash), algorithm=Utils.Constants['hash-algorithm'])
        return hash

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
                hashAsBytes = Utils.generateHashFromFile(f)
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
    def getTrackerFiles():
        
        f_trackerList = SharedObjects.F_DirTrack.listDirectory(conditional=lambda x: x.getNameWithoutExtension().startswith(APP_NAME))
        f_trackerList.sort(key=lambda x: str(x))
        
        return f_trackerList

    @staticmethod
    def getReferenceState():
        
        f_trackerList = Utils.getTrackerFiles()
        
        state = None
        if len(f_trackerList) != 0:
            f_trackerLast = f_trackerList[-1]
            state = JSON.fromFile(f_trackerLast)
            
        return state

class SharedObjects:
    
    F_CWD:FileUtils.File = None
    F_DirTrack:FileUtils.File = None
    F_Settings:FileUtils.File = None
    Settings:dict = None

    @staticmethod
    def initialize():
        SharedObjects.F_CWD = FileUtils.File.Utils.getWorkingDirectory()
        SharedObjects.F_DirTrack = SharedObjects.F_CWD.traverseDirectory(Utils.Constants['tracker-directory-name'])
        SharedObjects.F_Settings = SharedObjects.F_DirTrack.traverseDirectory('settings.json')

        if SharedObjects.F_Settings.isExists():
            SharedObjects.Settings = JSON.fromFile(SharedObjects.F_Settings)

    @staticmethod
    def cleanUp():
        pass

class CommandHandler:

    class Commit:
        
        @staticmethod
        def run():
            
            if not SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Directory is not initialized.")
            else:
                referenceState = Utils.getReferenceState()
                currentState = Utils.constructDirectoryState()
                
                isSaveRequired = False

                if referenceState is None:
                    isSaveRequired = True
                    Utils.Report.Info('First commit.')
                else:
                    delta = Utils.constructDelta(referenceState, currentState)
                    if delta['metadata']['is-directory-modified']:
                        isSaveRequired = True
                        Utils.Report.Delta(delta)
                    else:
                        Utils.Report.Error('There is no delta.')

                if isSaveRequired:
                    f_trackerBase = SharedObjects.F_DirTrack.traverseDirectory(Utils.Constants['tracker-file-name'])
                    f_trackerNew = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_trackerBase), iteratorLength=Utils.Constants['iterator-length']))
                    JSON.saveAs(currentState, f_trackerNew)
                
    class Init:

        def run():

            if SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Directory already initialized.")
            else:
                SharedObjects.F_DirTrack.makeDirectory()

                SharedObjects.Settings = Utils.Constants['default-settings'].copy()
                JSON.saveAs(SharedObjects.Settings, SharedObjects.F_Settings)

                Utils.Report.Info('Directory initialized successfully.')

    class Delta:
        
        @staticmethod
        def run():

            if not SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Directory is not initialized.")
            else:
                referenceState = Utils.getReferenceState()
                if referenceState is None:
                    Utils.Report.Error("No commit(s) found.")
                else:
                    currentState = Utils.constructDirectoryState()
                    delta = Utils.constructDelta(referenceState, currentState)
                    if delta['metadata']['is-directory-modified']:
                        Utils.Report.Delta(delta)
                    else:
                        Utils.Report.Error('There is no delta.')

    class Settings:

        @staticmethod
        def run(mode:str=None):

            if not SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Directory is not initialized.")
            else:

                if mode is not None:
                    SharedObjects.Settings['mode'] = mode
                
                FileUtils.File.Utils.recycle(SharedObjects.F_Settings)
                JSON.saveAs(SharedObjects.Settings, SharedObjects.F_Settings)

                Utils.Report.Info('Settings updated successfully.')
    
    class Optimize:

        @staticmethod
        def run():

            if not SharedObjects.F_DirTrack.isExists():
                Utils.Report.Error("Directory is not initialized.")
            else:
                f_trackerList = Utils.getTrackerFiles()
                if len(f_trackerList) > 1:
                    f_trackerLast = f_trackerList[-1]
                    for f_tracker in f_trackerList[:-1]:
                        FileUtils.File.Utils.recycle(f_tracker)
                    f_trackerBase = SharedObjects.F_DirTrack.traverseDirectory(Utils.Constants['tracker-file-name'])
                    f_trackerLastNewLocation = FileUtils.File(FileUtils.File.Utils.Path.modifyName(str(f_trackerBase), suffix=('-' + ('0' * Utils.Constants['iterator-length']))))
                    FileUtils.File.Utils.move(f_trackerLast, f_trackerLastNewLocation)

                Utils.Report.Info("Directory optimized successfully.")

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

@cli.command()
def init():
    '''
    Initialize a directory for tracking.
    '''
    SharedObjects.initialize()
    CommandHandler.Init.run()
    SharedObjects.cleanUp()

@cli.command()
@click.option('--mode', type=click.Choice(['fast', 'slow']), required=False, help='Switches between fast and slow mode.')
def settings(mode):
    '''
    Modify the settings of a (tracked) directory.
    '''
    SharedObjects.initialize()
    CommandHandler.Settings.run(mode)
    SharedObjects.cleanUp()

@cli.command()
def optimize():
    '''
    Optimizes a (tracked) directory by removing all but the last commit.
    '''
    SharedObjects.initialize()
    CommandHandler.Optimize.run()
    SharedObjects.cleanUp()

if __name__ == '__main__':
    cli()
