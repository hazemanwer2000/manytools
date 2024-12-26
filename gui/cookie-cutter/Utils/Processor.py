
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils

import time

# ? Command queue.
commandQueue = GConcurrency.Queue()

class INTERNAL:

    # ? Initialization parameter(s).
    class Parameters:
        f_video = None

def initialize(f_video:FileUtils.File):
    
    # ? (Short-)Initialization.
    INTERNAL.Parameters.f_video = f_video

def loop(thread:GConcurrency.Thread):
    
    # ? (Long-)Initialization.
    video = VideoUtils.Video(INTERNAL.Parameters.f_video)
    
    while(True):        
        
        # ? Wait until a command is present.
        command = commandQueue.dequeue()
        
        thread.notify(command)
