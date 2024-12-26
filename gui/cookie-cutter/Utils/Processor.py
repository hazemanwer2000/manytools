
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Base.ColorUtils as ColorUtils
import automatey.Base.TimeUtils as TimeUtils
import automatey.Base.ExceptionUtils as ExceptionUtils
import automatey.Utils.Validation as Validation

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
        def Assert(values, declaration):
            if not all(values):
                raise ExceptionUtils.ValidationError(declaration)

        @staticmethod
        def asColor(hexCode):
            return ColorUtils.Color.fromHEX(hexCode)

        @staticmethod
        def asTime(timeAsString):
            return TimeUtils.Time.createFromString(timeAsString)

    class CommandHandler:
        
        class Generate:
            
            class OptionValidation:
                
                def SepiaTone(cfgDict):
                    pass

                def Grayscale(cfgDict):
                    pass

                def BrightnessContrast(cfgDict):
                    cfgDict['Brightness-Factor'] = Validation.asFloat(cfgDict['Brightness-Factor'])
                    cfgDict['Contrast-Factor'] = Validation.asFloat(cfgDict['Brightness-Factor'])

                def GaussianBlur(cfgDict):
                    
                    cfgDict['Kernel-Size'] = Validation.asInt(cfgDict['Kernel-Size'])
                    # ? If (...) is less or equal to 1, or is not odd. 
                    INTERNAL.Validation.Assert([
                        (cfgDict['Kernel-Size'] <= 1),
                        ((cfgDict['Kernel-Size'] % 2) == 0),
                    ], 'Kernel size should be larger than 1, and odd.')

                def Sharpen(cfgDict):
                    cfgDict['Factor'] = Validation.asFloat(cfgDict['Factor'])

                    cfgDict['Kernel-Size'] = Validation.asInt(cfgDict['Kernel-Size'])
                    # ? If (...) is less or equal to 1, or is not odd. 
                    INTERNAL.Validation.Assert([
                        (cfgDict['Kernel-Size'] <= 1),
                        ((cfgDict['Kernel-Size'] % 2) == 0),
                    ], 'Kernel size should be larger than 1, and odd.')

                def Pixelate(cfgDict):
                    cfgDict['Factor'] = Validation.asFloat(cfgDict['Factor'])

                def AddBorder(cfgDict):
                    cfgDict['Color'] = INTERNAL.Validation.asColor(cfgDict['Color'])
                    
                    cfgDict['Thickness'] = Validation.asInt(cfgDict['Thickness'])
                    # ? (...)
                    INTERNAL.Validation.Assert([
                        (cfgDict['Thickness'] > 0),
                    ], 'Thickness must be larger than 0.')

                def Crop(cfgDict):
                    pass

                def Resize(cfgDict):
                    pass

                def VideoFade(cfgDict):
                    pass

                def AudioFade(cfgDict):
                    pass

                def AudioMute(cfgDict):
                    pass

                def TrimAtKeyframes(cfgDict):
                    pass

                def GIF(cfgDict):
                    pass
            
            @staticmethod
            def runner(commandStruct):
                
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
                    
                    # ? ? Options.
                    for option in commandStruct['Options']:
                        INTERNAL.CommandHandler.Generate.OptionValidation.__dict__[option['Name'].replace('-', '')](option['Cfg'])
                
                except:
                    resultStatus = 1
                    resultInfo = traceback.format_exc()
                
                return {
                    'Status' : resultStatus,
                    'Info' : resultInfo
                }

        mapping = {
            'Generate' : Generate.runner,
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
