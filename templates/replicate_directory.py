'''
Usage: A CLI tool, that replicates a directory, by processing each file in the input directory, and optionally,
        generating a corresponding file in the output directory.
'''

import click

import automatey.OS.FileUtils as FileUtils

def processFile(f_input:FileUtils.File, f_output:FileUtils.File):
    #REPLACE:
    pass

@click.command()
@click.option('--input', required=True, help='Input directory.')
@click.option('--output', required=True, help='Output path, where the output (i.e., replicated) directory will reside.')
def cli(input:str, output:str):
    '''
    #REPLACE: Replicates a directory, by processing each file in the input directory, and optionally, generating a corresponding file in the output directory.
    '''
    f_inputDir = FileUtils.File(input)
    f_baseOutputDir = FileUtils.File(output, f_inputDir.getName())
    f_outputDir = FileUtils.File(FileUtils.File.Utils.Path.iterateName(str(f_baseOutputDir))) 
    FileUtils.File.Utils.mapDirectoryFiles(f_inputDir, f_outputDir, processFile)

if __name__ == '__main__':
    cli()
