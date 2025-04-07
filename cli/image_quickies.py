
import click

from pprint import pprint

import automatey.OS.FileUtils as FileUtils
import automatey.Media.ImageUtils as ImageUtils
import automatey.OS.Specific.Windows as Windows

class Utils:

    @staticmethod
    def initialize():
        '''
        Initialization of all (shared) resource(s).
        '''
        pass

    @staticmethod
    def cleanUp():
        '''
        Clean-up of all (shared) resource(s).
        '''
        pass

class CommandHandler:

    class Tile:
        
        @staticmethod
        def run(f_inputDir:FileUtils.File, extension:str, rows:int, cols:int):
            f_list = f_inputDir.listDirectory(conditional=lambda x: ImageUtils.Image.Utils.isImage(f_inputDir))
            Windows.Utils.sort(f_list, key=lambda x: str(x))
            img_tiled = ImageUtils.Image.createByTiling(f_list, rows, cols)
            f_outputBase = f_inputDir.traverseDirectory('..', f_inputDir.getName() + '.' + extension)
            f_output = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_outputBase)))
            img_tiled.saveAs(f_output)

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
    Execute different image-processing command(s), quickly.
    '''
    pass

@cli.command()
@click.option('--input', required=True, help='Input directory.')
@click.option('--extension', required=True, help='Output file extension (without a dot).')
@click.option('--rows', required=True, help='Number of rows.', type=int)
@click.option('--cols', required=True, help='Number of columns.', type=int)
def tile(input, extension, rows, cols):
    '''
    Concat multiple (video) file(s).
    '''
    CommandHandler.Tile.run(FileUtils.File(input), extension, rows, cols)

if __name__ == '__main__':
    cli()
