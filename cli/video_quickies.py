
import click
import subprocess
import threading
import queue
import time
import os

import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Abstract.Graphics as Graphics
import automatey.Base.ColorUtils as ColorUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.Media.ImageUtils as ImageUtils
import automatey.Utils.RandomUtils as RandomUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.CLI as CLI
import automatey.OS.Specific.Windows as Windows

# ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Utils:
    
    Constants = {
        'cli' : {
            'text-color' : Graphics.TextColor(
                foreground=ColorUtils.Colors.PURPLE,
                background=ColorUtils.Colors.WHITE,
            )
        }
    }
    
    @staticmethod
    def executeCommand(*args) -> int:
        commandAsString = ' '.join(args)
        click.echo(f"\nCommand: {commandAsString}\n")
        proc = subprocess.Popen(commandAsString.split(sep=' '))
        proc.communicate()
        return proc.returncode

class FFMPEG:
    
    CommandTemplates = {
        'VideoConvert' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-crf {{{CRF}}}',
            r'-c:v libx264',
            r'-c:a aac',
            r'-vf pad=ceil(iw/2)*2:ceil(ih/2)*2',
            r'{{{OUTPUT-FILE}}}',
        ),
        'VideoConcat' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-loglevel error',
            r'-f concat',
            r'-safe 0',
            r'-i {{{LIST-FILE}}}',
            r'-c copy',
            r'{{{OUTPUT-FILE}}}',
        ),
    }

class CommandHandler:
    
    class Convert:
        
        @staticmethod
        def run(f_input:FileUtils.File, crf:int):
            f_output = FileUtils.File(
                FileUtils.File.Utils.Path.iterateName(
                    FileUtils.File.Utils.Path.modifyName(str(f_input), extension='mp4')
                )
            )
            commandFormatter = FFMPEG.CommandTemplates['VideoConvert'].createFormatter()
            commandFormatter.assertParameter('input-file', str(f_input))
            commandFormatter.assertParameter('crf', str(crf))
            commandFormatter.assertParameter('output-file', str(f_output))
            Utils.executeCommand(str(commandFormatter))

    class Thumbnail:
        
        @staticmethod
        def run(f_input:FileUtils.File, rows:int, cols:int):
            f_output = FileUtils.File(
                FileUtils.File.Utils.Path.iterateName(
                    FileUtils.File.Utils.Path.modifyName(str(f_input), extension='png')
                )
            )
            vid = VideoUtils.Video(f_input)
            vocalTimer = CLI.VocalTimer()
            
            # ? Generate thumbnail(s).
            thumbnailCount = rows * cols
            f_tmpDir = FileUtils.File.Utils.getTemporaryDirectory()
            f_thumbnailDir = f_tmpDir.traverseDirectory('thumbnails')
            vocalTimer.issueCommand(CLI.VocalTimer.Commands.StartTimer(label='Elapsed Time:', textColor=Utils.Constants['cli']['text-color']))
            vid.generateThumbnails(f_thumbnailDir, thumbnailCount)
            vocalTimer.issueCommand(CLI.VocalTimer.Commands.StopTimer())
            
            # ? Generate (joint) thumbnail.
            img_jointThumb = ImageUtils.Image.createByTiling(f_thumbnailDir.listDirectory(), rows, cols)
            img_jointThumb.resize(width=constants['thumbnail']['width'], height=-1)
            img_jointThumb.saveAs(f_output)
            
            # ? Clean-up (...)
            FileUtils.File.Utils.recycle(f_tmpDir)
            vocalTimer.issueCommand(CLI.VocalTimer.Commands.DestroyTimer())
            
    class Concat:
        
        @staticmethod
        def run(f_inputDir:FileUtils.File):
            
            # ? Get and sort list of input (video) file(s).
            f_joinList = f_inputDir.listDirectory()
            Windows.Utils.sort(f_joinList, key=lambda x: str(x))
            
            # ? Derive output file.
            f_outputBase = f_inputDir.traverseDirectory('..', f_inputDir.getName() + '.' + f_joinList[0].getExtension())
            f_output = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_outputBase)))
            
            # ? Create list (text) file.
            f_tmpDir = FileUtils.File.Utils.getTemporaryDirectory()
            f_txtList = f_tmpDir.traverseDirectory('list.txt')
            f_cwd = FileUtils.File.Utils.getWorkingDirectory()
            with f_txtList.openFile('wt') as f_txtListHandler:
                for f in f_joinList:
                    f_txtListHandler.writeLine("file '" + os.path.abspath(str(f)) + "'")

            # ? Generate (concat-video) file.
            commandFormatter = FFMPEG.CommandTemplates['VideoConcat'].createFormatter()
            commandFormatter.assertParameter('list-file', str(f_txtList))
            commandFormatter.assertParameter('output-file', str(f_output))
            Utils.executeCommand(str(commandFormatter))

            # ? Clean-up (...)
            FileUtils.File.Utils.recycle(f_tmpDir)

@click.group()
def cli():
    '''
    Execute different video-edit command(s), quickly.
    '''
    pass

@cli.command()
@click.option('--input', required=True, help='Input directory.')
def concat(input):
    '''
    Concat multiple (video) file(s).
    '''
    CommandHandler.Concat.run(FileUtils.File(input))

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--crf', required=True, help='CRF value.', type=int)
def convert(input, crf):
    '''
    Convert a video into a '.mp4' file.
    '''
    CommandHandler.Convert.run(FileUtils.File(input), crf)

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--rows', required=True, help='Number of rows.', type=int)
@click.option('--cols', required=True, help='Number of columns.', type=int)
def thumbnail(input, rows, cols):
    '''
    Create a thumbnail for a (video) file.
    '''
    CommandHandler.Thumbnail.run(FileUtils.File(input), rows, cols)

if __name__ == '__main__':
    cli()