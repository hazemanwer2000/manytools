
import click

import subprocess
import os
import shlex
from pprint import pprint
import typing

import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.Utils.ColorUtils as ColorUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.Media.ImageUtils as ImageUtils
import automatey.Utils.MathUtils as MathUtils
import automatey.Formats.JSON as JSON
import automatey.Utils.CLI as CLI
import automatey.Utils.StringUtils as StringUtils
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.OS.Specific.Windows as Windows
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Formats.SRT as SRT

# ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Utils:
    
    vocalTimer = None
    
    Constants = {
        'cli' : {
            'text-color' : AbstractGraphics.TextColor(
                foreground=ColorUtils.Colors.WHITE,
                background=ColorUtils.Colors.PURPLE,
            )
        },
        'command' : {
            'thumbnail' : {
                'output-extension' : 'jpg',
            }
        }
    }
    
    @staticmethod
    def executeCommand(*args) -> int:
        commandAsString = ' '.join(args)
        click.echo(f"\nCommand: {commandAsString}\n")
        proc = subprocess.Popen(shlex.split(commandAsString))
        proc.communicate()
        return proc.returncode

    @staticmethod
    def initialize():
        '''
        Initialization of all (shared) resource(s).
        '''
        Utils.vocalTimer = CLI.VocalTimer()

    @staticmethod
    def cleanUp():
        '''
        Clean-up of all (shared) resource(s).
        '''
        Utils.vocalTimer.issueCommand(CLI.VocalTimer.Commands.DestroyTimer())

class FFMPEG:
    
    CommandTemplates = {
        'VideoSpeed' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-crf {{{CRF}}}',
            r'-filter_complex "[0:v]setpts={{{REVERSE-SPEED-FACTOR}}}*PTS[v]; [0:a]atempo={{{SPEED-FACTOR}}}[a]"',
            r'-map "[v]"',
            r'-map "[a]"',
            r'{{{OUTPUT-FILE}}}',
        ),
        'VideoSpeedNoAudio' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-crf {{{CRF}}}',
            r'-filter_complex "[0:v]setpts={{{REVERSE-SPEED-FACTOR}}}*PTS[v]"',
            r'-map "[v]"',
            r'{{{OUTPUT-FILE}}}',
        ),
        'VideoConvert' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-crf {{{CRF}}}',
            r'-c:v libx264',
            r'-c:a aac',
            r'-vf pad=ceil(iw/2)*2:ceil(ih/2)*2,scale={{{WIDTH}}}:{{{HEIGHT}}}',
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
        'VideoNoMetadata' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-loglevel error',
            r'-i {{{INPUT-FILE}}}',
            r'-map_metadata -1',
            r'-map_chapters -1',
            r'-codec copy',
            r'{{{OUTPUT-FILE}}}',
        ),
        'VideoFilter:BlackAndWhite' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-f lavfi -i color={{{THRESHOLD-COLOR}}}:s={{{VIDEO-WIDTH}}}x{{{VIDEO-HEIGHT}}}',
            r'-f lavfi -i color=black:s={{{VIDEO-WIDTH}}}x{{{VIDEO-HEIGHT}}}',
            r'-f lavfi -i color=white:s={{{VIDEO-WIDTH}}}x{{{VIDEO-HEIGHT}}}',
            r'-filter_complex "[0:v] format=gray [gray]; [gray][1:v][2:v][3:v] threshold"',
            r'-crf {{{CRF}}}',
            r'-c:v libx264',
            r'-c:a aac',
            r'{{{OUTPUT-FILE}}}',
        ),
        'AudioMute' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-an',
            r'-c:v copy',
            r'{{{OUTPUT-FILE}}}',
        ),
        'AudioReplace' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-VIDEO-FILE}}}',   
            r'-i {{{INPUT-AUDIO-FILE}}}',   
            r'-c:v copy',
            r'-c:a copy',
            r'-map 0:v:0', 
            r'-map 1:a:0', 
            r'-shortest', 
            r'{{{OUTPUT-VIDEO-FILE}}}', 
        ),
        'AudioConvert' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-c:a aac',
            r'-b:a 256k',
            r'{{{OUTPUT-FILE}}}', 
        ),
        'AudioExtract' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-VIDEO-FILE}}}',
            r'-vn',
            r'-acodec copy',
            r'{{{OUTPUT-AUDIO-FILE}}}', 
        ),
    }

    @staticmethod
    def writeMetadata(chapters:typing.List['SRT.Subtitle']) -> str:
        '''
        Write the metadata of a video, in FFMPEG's specific metadata format.
        '''
        # ? Setup writer.
        writer = StringUtils.Writer()
        # ? ? FFMPEG's first version of its metadata format.
        writer.write(';FFMETADATA1')

        # ? For each chapter (...)
        for chapter in chapters:
            writer.writeLines([
                '[CHAPTER]',
                'TIMEBASE=1/1000',
                f"START={str(int(chapter.getStartTime().toMilliseconds()))}",
                f"END={str(int(chapter.getEndTime().toMilliseconds()))}",
                f"TITLE={chapter.getText()}",
                ''
            ])

        return str(writer).strip()

class CommandHandler:
    
    class Filter:

        class BlackAndWhite:
            
            @staticmethod
            def run(f_input:FileUtils.File, crf:int, threshold:int):

                # ? (...)
                f_output = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input), extension='mp4')
                    )
                )
                
                # ? Initialize video.
                video = VideoUtils.Video(f_input)
                
                # ? Construct command.
                commandFormatter = FFMPEG.CommandTemplates['VideoFilter:BlackAndWhite'].createFormatter()
                commandFormatter.assertParameter('input-file', str(f_input))
                commandFormatter.assertParameter('crf', str(crf))
                commandFormatter.assertParameter('output-file', str(f_output))
                # ? ? Assert threshold color.
                thresholdColor = ColorUtils.Color(threshold, threshold, threshold)
                commandFormatter.assertParameter('threshold-color', '0x' + thresholdColor.asHEX())
                # ? ? Assert video width and height.
                width, height = video.getDimensions()
                commandFormatter.assertParameter('video-width', str(width))
                commandFormatter.assertParameter('video-height', str(height))
                
                # ? Execute command.
                Utils.executeCommand(str(commandFormatter))
    
    class Convert:
        
        @staticmethod
        def run(f_input:FileUtils.File, crf:int, width:int, height:int):
            
            f_inputList = []
            f_outputList = []
            
            # ? If input is a directory, (...)
            if f_input.isDirectory():
            
                # ? Setup I/O directories.
                f_inputDirectory = f_input 
                f_outputDirectory = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_inputDirectory)))
                f_outputDirectory.makeDirectory()
                
                # ? Collect I/O file(s).
                f_inputList += f_input.listDirectory(conditional=lambda x: x.isFile())
                for path_inputFile_relative in f_input.listDirectoryRelatively(conditional=lambda x: x.isFile()):
                    f_outputFile = f_outputDirectory.traverseDirectory(FileUtils.File.Utils.Path.modifyName(path_inputFile_relative, extension='mp4'))
                    f_outputList.append(f_outputFile)
            
            else:
                f_inputFile = f_input
                f_outputFile = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input), extension='mp4')
                    )
                )
                f_inputList.append(f_inputFile)
                f_outputList.append(f_outputFile)
            
            # ? Convert each file.
            for f_inputFile, f_outputFile in zip(f_inputList, f_outputList):
                commandFormatter = FFMPEG.CommandTemplates['VideoConvert'].createFormatter()
                commandFormatter.assertParameter('input-file', str(f_inputFile))
                commandFormatter.assertParameter('crf', str(crf))
                commandFormatter.assertParameter('width', str(width))
                commandFormatter.assertParameter('height', str(height))
                commandFormatter.assertParameter('output-file', str(f_outputFile))
                Utils.executeCommand(str(commandFormatter))

    class Thumbnail:
        
        @staticmethod
        def run(f_input:FileUtils.File, rows:int, cols:int, timestampOptions:str, aspectRatio:float, f_output:FileUtils.File=None):
            
            commandConstants = Utils.Constants['command']['thumbnail']
            
            if f_output is None:
                f_output = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input), extension=commandConstants['output-extension'])
                    )
                )
            vid = VideoUtils.Video(f_input)
            
            # ? Construct 'ThumbnailTimestampAttributes'.
            thumbnailTimestampAttributes = None
            if timestampOptions is not None:
                tsOptionAlignment, tsOptionColorHEXCode = timestampOptions.lower().split(',')
                thumbnailTimestampAttributes = VideoUtils.ThumbnailTimestampAttributes(
                    textColor=ColorUtils.Color.fromHEX(tsOptionColorHEXCode),
                    offsetRatio=AbstractGraphics.Point(0.01, 0.03),
                    cornerAlignment=AbstractGraphics.Alignment.Corner.__dict__[StringUtils.Case.Snake2Pascal(tsOptionAlignment)],
                    sizeRatio=MathUtils.correlate(cols, (4, 0.075), (2, 0.045))
                )
            
            # ? Generate thumbnail(s).
            thumbnailCount = rows * cols
            f_tmpDir = FileUtils.File.Utils.getTemporaryDirectory()
            f_thumbnailDir = f_tmpDir.traverseDirectory('thumbnails')
            Utils.vocalTimer.issueCommand(CLI.VocalTimer.Commands.StartTimer(label='Elapsed Time:', textColor=Utils.Constants['cli']['text-color']))
            vid.generateThumbnails(f_thumbnailDir, thumbnailCount, thumbnailTimestampAttributes)
            Utils.vocalTimer.issueCommand(CLI.VocalTimer.Commands.StopTimer())

            # ? Determine (joint) thumbnail width and height.
            thumbnailWidth = constants['thumbnail']['width']
            thumbnailHeight = -1
            if aspectRatio != None:
                thumbnailHeight = int((thumbnailWidth / aspectRatio) * (rows / cols))
            
            # ? Generate (joint) thumbnail.
            img_jointThumb = ImageUtils.Image.createByTiling(f_thumbnailDir.listDirectory(), rows, cols)
            img_jointThumb.resize(width=thumbnailWidth, height=thumbnailHeight)
            img_jointThumb.saveAs(f_output)
            
            # ? Clean-up (...)
            FileUtils.File.Utils.recycle(f_tmpDir)

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

    class Screenshots:
        
        @staticmethod
        def run(f_input:FileUtils.File, offset:float):
            
            # ? Derive output directory.
            f_outputDirBase = f_input.traverseDirectory('..', f_input.getNameWithoutExtension())
            f_outputDir = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_outputDirBase)))

            # ? Generate thumbnails.
            video = VideoUtils.Video(f_input)
            N = int(video.getDuration().toSeconds() / offset) - 1
            video.generateThumbnails(f_outputDir, N)

    class NoMetadata:

        @staticmethod
        def run(f_input:FileUtils.File):

            # ? Derive output file.
            f_outputBase = f_input.traverseDirectory('..', f_input.getName())
            f_output = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_outputBase)))

            # ? Generate (concat-video) file.
            commandFormatter = FFMPEG.CommandTemplates['VideoNoMetadata'].createFormatter()
            commandFormatter.assertParameter('input-file', str(f_input))
            commandFormatter.assertParameter('output-file', str(f_output))
            Utils.executeCommand(str(commandFormatter))

    class Audio:

        class Mute:

            @staticmethod
            def run(f_input:FileUtils.File):

                # ? (...)
                f_output = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input))
                    )
                )

                # ? Generate.
                commandFormatter = FFMPEG.CommandTemplates['AudioMute'].createFormatter()
                commandFormatter.assertParameter('input-file', str(f_input))
                commandFormatter.assertParameter('output-file', str(f_output))
                Utils.executeCommand(str(commandFormatter))

        class Extract:

            @staticmethod
            def run(f_input:FileUtils.File, outputExtension:str):

                # ? (...)
                f_output = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input), extension=outputExtension)
                    )
                )

                # ? Generate.
                commandFormatter = FFMPEG.CommandTemplates['AudioExtract'].createFormatter()
                commandFormatter.assertParameter('input-video-file', str(f_input))
                commandFormatter.assertParameter('output-audio-file', str(f_output))
                Utils.executeCommand(str(commandFormatter))

        class Replace:

            @staticmethod
            def run(f_input:FileUtils.File, f_audio:FileUtils.File):

                # ? (...)
                f_output = FileUtils.File(
                    FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(f_input))
                    )
                )

                # ? Generate.
                commandFormatter = FFMPEG.CommandTemplates['AudioReplace'].createFormatter()
                commandFormatter.assertParameter('input-video-file', str(f_input))
                commandFormatter.assertParameter('input-audio-file', str(f_audio))
                commandFormatter.assertParameter('output-video-file', str(f_output))
                Utils.executeCommand(str(commandFormatter))

        class Convert:

            @staticmethod
            def run(f_input:FileUtils.File):

                f_inputList = []
                f_outputList = []
                
                # ? If input is a directory, (...)
                if f_input.isDirectory():
                
                    # ? Setup I/O directories.
                    f_inputDirectory = f_input 
                    f_outputDirectory = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_inputDirectory)))
                    f_outputDirectory.makeDirectory()
                    
                    # ? Collect I/O file(s).
                    f_inputList += f_input.listDirectory(conditional=lambda x: x.isFile())
                    for path_inputFile_relative in f_input.listDirectoryRelatively(conditional=lambda x: x.isFile()):
                        f_outputFile = f_outputDirectory.traverseDirectory(FileUtils.File.Utils.Path.modifyName(path_inputFile_relative, extension='m4a'))
                        f_outputList.append(f_outputFile)
                
                else:
                    f_inputFile = f_input
                    f_outputFile = FileUtils.File(
                        FileUtils.File.Utils.Path.iterateName(
                            FileUtils.File.Utils.Path.modifyName(str(f_input), extension='m4a')
                        )
                    )
                    f_inputList.append(f_inputFile)
                    f_outputList.append(f_outputFile)
                
                # ? Convert each file.
                for f_inputFile, f_outputFile in zip(f_inputList, f_outputList):
                    commandFormatter = FFMPEG.CommandTemplates['AudioConvert'].createFormatter()
                    commandFormatter.assertParameter('input-file', str(f_inputFile))
                    commandFormatter.assertParameter('output-file', str(f_outputFile))
                    Utils.executeCommand(str(commandFormatter))

    class Speed:

        @staticmethod
        def run(f_input:FileUtils.File, speedFactor:float, crf:int, isNoAudio:bool):

            # ? (...)
            f_output = FileUtils.File(
                FileUtils.File.Utils.Path.iterateName(
                    FileUtils.File.Utils.Path.modifyName(str(f_input))
                )
            )

            # ? Generate.
            commandFormatter = FFMPEG.CommandTemplates['VideoSpeedNoAudio' if isNoAudio else 'VideoSpeed'].createFormatter()
            commandFormatter.assertParameter('input-file', str(f_input))
            commandFormatter.assertParameter('speed-factor', f"{speedFactor:.6f}")
            commandFormatter.assertParameter('reverse-speed-factor', f"{(1/speedFactor):.6f}")
            commandFormatter.assertParameter('crf', str(crf))
            commandFormatter.assertParameter('output-file', str(f_output))
            Utils.executeCommand(str(commandFormatter))

class CustomGroup(click.Group):
    def invoke(self, ctx):
        Utils.initialize()
        try:
            super().invoke(ctx)
        finally:
            Utils.cleanUp()

@click.group(cls=CustomGroup)
def cli():
    '''
    Execute different video-edit command(s), quickly.
    '''
    pass

@cli.group()
def filter():
    '''
    Apply (complex) filter(s) to (video) file(s).
    '''
    pass

@filter.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--crf', required=True, help='CRF value.', type=int)
@click.option('--threshold', required=True, help='Spans from 0 to 255.', type=int)
def black_and_white(input, crf, threshold):
    '''
    Forces all pixel(s) to turn, either black or white, based on a threshold value.
    '''
    CommandHandler.Filter.BlackAndWhite.run(FileUtils.File(input), crf, threshold)

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
@click.option('--width', required=False, help="Width. '-1' for auto-calculation, based on aspect ratio.", type=int, default=-1)
@click.option('--height', required=False, help="Height. '-1' for auto-calculation, based on aspect ratio.", type=int, default=-1)
def convert(input, crf, width, height):
    '''
    Convert a video, or a directory of video(s), into '.mp4' file(s).
    '''
    CommandHandler.Convert.run(FileUtils.File(input), crf, width, height)

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--factor', required=True, help='Speed-up factor. For example, "2" will make the video play twice as fast.', type=float)
@click.option('--crf', required=False, help='CRF value.', type=int)
@click.option('--no-audio', is_flag=True, help='Whether the video has an audio stream.')
def speed(input, factor, crf, no_audio):
    '''
    Change the speed of a video.
    '''
    CommandHandler.Speed.run(FileUtils.File(input), factor, crf, no_audio)

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--rows', required=True, help='Number of rows.', type=int)
@click.option('--cols', required=True, help='Number of columns.', type=int)
@click.option('--timestamps', help='Specifies options for overlaying timestamps. Format is "ALIGNMENT,COLOR". For example, "bottom-left,#000000"', type=str)
@click.option('--aspect_ratio', help='Force aspect ratio of thumbnail.', type=str)
def thumbnail(input, rows, cols, timestamps, aspect_ratio):
    '''
    Create a thumbnail for a (video) file.
    '''
    if aspect_ratio != None:
        aspect_ratio = float(eval(aspect_ratio))
    CommandHandler.Thumbnail.run(FileUtils.File(input), rows, cols, timestamps, aspect_ratio)

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--offset', required=True, help='Offset between every screenshot, in seconds.', type=float)
def screenshots(input, offset):
    '''
    Create 'N' screenshots of a video.
    '''
    CommandHandler.Screenshots.run(FileUtils.File(input), offset)

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
def no_metadata(input):
    '''
    Remove all metadata from video.
    '''
    CommandHandler.NoMetadata.run(FileUtils.File(input))

@cli.group()
def audio():
    '''
    Manipulate audio.
    '''
    pass

@audio.command()
@click.option('--input', required=True, help='Input (video) file.')
def mute(input):
    '''
    Removes audio from a video (i.e., mutes the video).
    '''
    CommandHandler.Audio.Mute.run(FileUtils.File(input))

@audio.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--extension', required=False, default='m4a', help='Extension of output file.')
def extract(input, extension):
    '''
    Extracts audio from a video, without any re-encoding.
    '''
    CommandHandler.Audio.Extract.run(FileUtils.File(input), extension)

@audio.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--audio', required=True, help='Input (audio) file.')
def replace(input, audio):
    '''
    Replace audio of a video with another audio.
    '''
    CommandHandler.Audio.Replace.run(FileUtils.File(input), FileUtils.File(audio))

@audio.command()
@click.option('--input', required=True, help='Input (audio) file.')
def convert(input):
    '''
    Convert an input file, or a directory of input file(s), into '.m4a' file(s).
    '''
    CommandHandler.Audio.Convert.run(FileUtils.File(input))

if __name__ == '__main__':
    cli()
