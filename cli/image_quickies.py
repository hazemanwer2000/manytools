
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

    class Replicator:

        @staticmethod
        def run(f_input:FileUtils.File, mappingFcn):
            if f_input.isDirectory():
                f_outputDir = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_input)))
                FileUtils.File.Utils.mapDirectoryFiles(f_input, f_outputDir, mappingFcn)
            else:
                f_output = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_input)))
                mappingFcn(f_input, f_output)

    class MappingFcns:

        class Filter:

            @staticmethod
            def shades_of_grey(f_src:FileUtils.File, f_dst:FileUtils.File):
                if ImageUtils.Image.Utils.isImage(f_src):
                    img = ImageUtils.Image(f_src)
                    img.blackWhite()
                    img.grayscale()
                    img.saveAs(f_dst)

            @staticmethod
            def black_and_white(f_src:FileUtils.File, f_dst:FileUtils.File):
                if ImageUtils.Image.Utils.isImage(f_src):
                    img = ImageUtils.Image(f_src)
                    img.grayscale()
                    img.blackWhite()
                    img.saveAs(f_dst)

class CommandHandler:

    class Tile:
        
        @staticmethod
        def run(f_inputDir:FileUtils.File, extension:str, rows:int, cols:int):
            f_list = f_inputDir.listDirectory(conditional=lambda x: ImageUtils.Image.Utils.isImage(x))
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

@cli.group()
def filter():
    '''
    Apply different filter(s).
    '''
    pass

@filter.command()
@click.option('--input', required=True, help='Input file, or directory.')
def shades_of_grey(input):
    '''
    A black-and-white filter, followed by a grayscale filter.
    '''
    Utils.Replicator.run(FileUtils.File(input), Utils.MappingFcns.Filter.shades_of_grey)

@filter.command()
@click.option('--input', required=True, help='Input file, or directory.')
def black_and_white(input):
    '''
    A black-and-white filter.
    '''
    Utils.Replicator.run(FileUtils.File(input), Utils.MappingFcns.Filter.black_and_white)

if __name__ == '__main__':
    cli()
