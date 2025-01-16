
import click
import subprocess
import threading
import queue
import time

import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.Media.ImageUtils as ImageUtils
import automatey.Utils.RandomUtils as RandomUtils
import automatey.Base.TimeUtils as TimeUtils
import automatey.Formats.JSON as JSON

# ? Get app's root directory.
f_this = FileUtils.File(__file__)
f_appDir = FileUtils.File(__file__).traverseDirectory('..', f_this.getNameWithoutExtension())

# ? Read constant(s).
f_constants = f_appDir.traverseDirectory('constants.json')
constants = JSON.fromFile(f_constants)

class Utils:
    
    @staticmethod
    def executeCommand(*args) -> int:
        commandAsString = ' '.join(args)
        click.echo(f"\nCommand: {commandAsString}\n")
        proc = subprocess.Popen(commandAsString.split(sep=' '))
        proc.communicate()
        return proc.returncode
    
    @staticmethod
    def getTemporaryDirectory():
        f_tmpDir = FileUtils.File.Utils.getTemporaryDirectory().traverseDirectory(RandomUtils.Generation.String(7))
        f_tmpDir.makeDirectory()
        return f_tmpDir

    class VocalTimer:
        '''
        A vocal timer, for CLI application(s) with long I/O operation(s).
        '''
        
        INTERNAL_Constants = {
            # (!) Note: In Seconds.
            'sleep-time' : {
                'upper' : 1.2,
                'lower' : 0.8,
            },
        }
        
        def __init__(self):
            
            # ? Initialize large object(s).
            self.queue = queue.Queue()
            self.thread = threading.Thread(target=self.INTERNAL_runner)
            
            # ? Start the thread.
            self.thread.start()
        
        def INTERNAL_runner(self):
            
            # ? Initialize working variable(s).
            isHalted = True
            referenceTime = None
            message = None
            
            while (True):
                  
                # ? Check if there's anything pending in the queue.
                if not self.queue.empty():
                    item = self.queue.get()
                    if item['command'] == 'kill':
                        break
                    elif item['command'] == 'stop':
                        isHalted = True
                    elif item['command'] == 'start':
                        isHalted = False
                        referenceTime = item['args']['reference-time']
                        message = item['args']['message']
                
                # ? Report, if not halted.
                if not isHalted:
                    
                    time.sleep(
                        RandomUtils.Generation.Float(
                            Utils.VocalTimer.INTERNAL_Constants['sleep-time']['lower'],
                            Utils.VocalTimer.INTERNAL_Constants['sleep-time']['upper'],
                        )
                    )
                    deltaTime = TimeUtils.Time.getEpochTime() - referenceTime
                    print(((message + ': ') if (message != None) else '') + str(deltaTime))
        
        def start(self, message=None):
            self.queue.put(item={
                'command' : 'start',
                'args' : {
                    'reference-time' : TimeUtils.Time.getEpochTime(),
                    'message' : message,
                },
            })
        
        def stop(self):
            self.queue.put(item={
                'command' : 'stop',
                'args' : None,
            })
        
        def kill(self):
            self.queue.put(item={
                'command' : 'kill',
                'args' : None,
            })

class FFMPEG:
    
    CommandTemplates = {
        'Convert' : ProcessUtils.CommandTemplate(
            r'ffmpeg',
            r'-hide_banner',
            r'-i {{{INPUT-FILE}}}',
            r'-crf {{{CRF}}}',
            r'-c:v libx264',
            r'-c:a aac',
            r'-vf pad=ceil(iw/2)*2:ceil(ih/2)*2',
            r'{{{OUTPUT-FILE}}}',
        )
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
            commandFormatter = FFMPEG.CommandTemplates['Convert'].createFormatter()
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
            vocalTimer = Utils.VocalTimer()
            
            # ? Generate thumbnail(s).
            thumbnailCount = rows * cols
            f_tmpDir = Utils.getTemporaryDirectory()
            f_thumbnailDir = f_tmpDir.traverseDirectory('thumbnails')
            vocalTimer.start(message='Elapsed Time')
            vid.generateThumbnails(f_thumbnailDir, thumbnailCount)
            vocalTimer.stop()
            
            # ? Generate (joint) thumbnail.
            img_jointThumb = ImageUtils.Image.createByTiling(f_thumbnailDir.listDirectory(), rows, cols)
            img_jointThumb.resize(width=constants['thumbnail']['width'], height=-1)
            img_jointThumb.saveAs(f_output)
            
            # ? Clean-up (...)
            FileUtils.File.Utils.recycle(f_tmpDir)
            vocalTimer.kill()
            
@click.group()
def cli():
    '''
    Execute different video-edit command(s), quickly.
    '''
    pass

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