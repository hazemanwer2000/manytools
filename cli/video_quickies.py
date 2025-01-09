
import click
import subprocess

import automatey.OS.FileUtils as FileUtils
import automatey.OS.ProcessUtils as ProcessUtils

class Utils:
    
    @staticmethod
    def executeCommand(*args) -> int:
        commandAsString = ' '.join(args)
        click.echo(f"\nCommand: {commandAsString}\n")
        proc = subprocess.Popen(commandAsString.split(sep=' '))
        proc.communicate()
        return proc.returncode

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
            f_output = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_input)))
            commandFormatter = FFMPEG.CommandTemplates['Convert'].createFormatter()
            commandFormatter.assertParameter('input-file', str(f_input))
            commandFormatter.assertParameter('crf', str(crf))
            commandFormatter.assertParameter('output-file', str(f_output))
            Utils.executeCommand(str(commandFormatter))

@click.group()
def cli():
    '''
    Execute different video-edit command(s), quickly.
    '''
    pass

@cli.command()
@click.option('--input', required=True, help='Input (video) file.')
@click.option('--crf', required=True, help='CRF value.')
def convert(input, crf):
    '''
    Convert a video into a '.mp4' file.
    '''
    CommandHandler.Convert.run(FileUtils.File(input), crf)

if __name__ == '__main__':
    cli()