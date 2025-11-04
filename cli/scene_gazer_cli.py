
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
import automatey.Media.VideoUtils as VideoUtils
import automatey.Utils.ExceptionUtils as ExceptionUtils
import automatey.Utils.CLI as CLI

from pprint import pprint

class Utils:

    @staticmethod
    def isVideoFile(f:FileUtils.File):
        return f.isFile() and VideoUtils.Video.Utils.isVideo(f)
    
    class Metadata:

        @staticmethod
        def create(f_video:FileUtils.File) -> bool:
            '''
            Creates metadata file that corresponds to a specific video file, if non-existent.

            Returns `False` if already existent, otherwise `True`. 
            '''
            isNewlyCreated = False

            # ? Create metadata directory, if non-existent.
            f_metadataDir = f_video.traverseDirectory('..', '.metadata')
            if not f_metadataDir.isExists():
                f_metadataDir.makeDirectory()
            elif not f_metadataDir.isDirectory():
                raise ExceptionUtils.ValidationError(f"Metadata directory could not be created: '{str(f_metadataDir)}'")
            
            # ? Create metadata file, if non-existent.
            f_metadata = f_metadataDir.traverseDirectory(f_video.getNameWithoutExtension() + '.json')
            if not f_metadata.isExists():
                JSON.saveAs(dict(), f_metadata)
                isNewlyCreated = True
            
            return isNewlyCreated

@click.group()
def cli():
    '''
    A CLI interface to the `scene-gazer` tool.
    '''
    pass
    
@cli.command()
@click.option('--input', required=True, help='Input directory or file.')
def init(input):
    '''
    Initializes a directory of video file(s), with empty metadata file(s), corresponding to each video file.

    Note: If a metadata file already exists, it is not overwritten.
    '''
    # ? Confirm user wishes to apply changes.
    if CLI.Input.Repeater(lambda: CLI.Input.getBool('Are you sure? [yes/no]: ')) == False:
        print("Nothing changed.")
        exit(0)

    # ? Collect all video file(s).
    f_root = FileUtils.File(input)
    f_list = []
    if Utils.isVideoFile(f_root):
        f_list.append(f_root)
    elif f_root.isDirectory():
        f_list.extend(f_root.listDirectory(isRecursive=True, conditional=Utils.isVideoFile))

    # ? Create metadata file, for each video file.
    newlyCreatedCount = 0
    for f_video in f_list:
        if Utils.Metadata.create(f_video):
            newlyCreatedCount += 1

    print(f"{newlyCreatedCount} newly created out of {len(f_list)}")

if __name__ == '__main__':
    cli()
