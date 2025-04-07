
import click

from pprint import pprint

import automatey.OS.FileUtils as FileUtils

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
        def run(f_inputDir:FileUtils.File, rows:int, cols:int):
            pass

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
@click.option('--rows', required=True, help='Number of rows.', type=int)
@click.option('--cols', required=True, help='Number of columns.', type=int)
def tile(input, rows, cols):
    '''
    Concat multiple (video) file(s).
    '''
    CommandHandler.Tile.run(FileUtils.File(input), rows, cols)

if __name__ == '__main__':
    cli()
