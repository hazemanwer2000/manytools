
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Base.ColorUtils as ColorUtils
import automatey.Base.TimeUtils as TimeUtils

import time
import traceback

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

    class Validation:

        @staticmethod
        def asColor(hexCode):
            return ColorUtils.Color.fromHEX(hexCode)

        @staticmethod
        def asTime(timeAsString):
            return TimeUtils.Time.createFromString(timeAsString)

    class CommandHandler:
        
        @staticmethod
        def generate(commandStruct):
            
            resultStatus = 0
            resultInfo = ''
            
            # ? Clean-up arguments.
            try:
                
                # ? ? Process time-entries.
                for trimTimeEntry in commandStruct['Trim-Times']:
                    if trimTimeEntry['Start-Time'] != '':
                        trimTimeEntry['Start-Time'] = INTERNAL.Validation.asTime(trimTimeEntry['Start-Time'])
                    if trimTimeEntry['End-Time'] != '':
                        trimTimeEntry['End-Time'] = INTERNAL.Validation.asTime(trimTimeEntry['End-Time'])
            
            except:
                resultStatus = 1
                resultInfo = traceback.format_exc()
            
            return {
                'Status' : resultStatus,
                'Info' : resultInfo
            }

        mapping = {
            'Generate' : generate,
        }

    # ? Initialization parameter(s).
    class Parameters:
        f_video = None
        f_videoInfoTemplate = None

    @staticmethod
    def longInitialize():
        
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

def initialize(f_video:FileUtils.File, f_videoInfoTemplate:FileUtils.File):
    
    # ? (Short-)Initialization.
    INTERNAL.Parameters.f_video = f_video
    INTERNAL.Parameters.f_videoInfoTemplate = f_videoInfoTemplate

def loop(thread:GConcurrency.Thread):
    
    INTERNAL.longInitialize()
    
    while(True):        
        
        # ? Wait until a command is present.
        commandStruct = commandQueue.dequeue()
        
        # ? Pass command to (respective) handler.
        result = INTERNAL.CommandHandler.mapping[commandStruct['Command']](commandStruct['Arguments'])
        
        # ? Construct return data.
        returnStruct = {
            'Command' : commandStruct['Command'],
            'Result' : result,
        }
        
        # ? Send notification.
        thread.notify(returnStruct)
