
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils

import time

# ? Command queue.
commandQueue = GConcurrency.Queue()

# ? Initialization parameter(s).
f_video = None

def initialize(_f_video:FileUtils.File):
    
    # ? (Short-)Initialization.
    global f_video
    f_video = _f_video

def loop(thread:GConcurrency.Thread):
    
    # ? (Long-)Initialization.
    video = VideoUtils.Video(f_video)
    
    while(True):        
        
        # ? Wait until a command is present.
        command = commandQueue.dequeue()
        
        thread.notify(command)
