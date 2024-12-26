
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.ProcessUtils as ProcessUtils

import time

# ? Video Informaiton, has to be initialized by thread.
class VideoInformation:

    isInitialized = False

    keyframes = None
    fps = None
    dimensions = None
    duration = None
    
    summary = None

# ? Command queue.
commandQueue = GConcurrency.Queue()

class INTERNAL:

    # ? Initialization parameter(s).
    class Parameters:
        f_video = None
        f_videoInfoTemplate = None

def initialize(f_video:FileUtils.File, f_videoInfoTemplate:FileUtils.File):
    
    # ? (Short-)Initialization.
    INTERNAL.Parameters.f_video = f_video
    INTERNAL.Parameters.f_videoInfoTemplate = f_videoInfoTemplate

def loop(thread:GConcurrency.Thread):
    
    # ? (Long-)Initialization.
    video = VideoUtils.Video(INTERNAL.Parameters.f_video)
    
    # ? Initialization of video information.
    VideoInformation.keyframes = video.getKeyframes()
    VideoInformation.fps = video.getFPS()
    VideoInformation.dimensions = video.getDimensions()
    VideoInformation.duration = video.getDuration()
    # ? ? 
    summaryFormatter = ProcessUtils.FileTemplate.fromFile(INTERNAL.Parameters.f_videoInfoTemplate).createFormatter()
    summaryFormatter.assertParameter('fps', f"{VideoInformation.fps:.3f}")
    summaryFormatter.assertParameter('size', str(VideoInformation.dimensions))
    VideoInformation.summary = str(summaryFormatter)
    # ? ? (...)
    VideoInformation.isInitialized = True
    
    while(True):        
        
        # ? Wait until a command is present.
        command = commandQueue.dequeue()
        
        thread.notify(command)
