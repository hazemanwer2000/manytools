
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Base.ColorUtils as ColorUtils
import automatey.Base.TimeUtils as TimeUtils
import automatey.Base.ExceptionUtils as ExceptionUtils
import automatey.Utils.Validation as Validation
import automatey.Utils.StringUtils as StringUtils

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
        def Assert(value, conditionals, declaration):
            for conditional in conditionals:
                if not conditional(value):
                    raise ExceptionUtils.ValidationError(declaration)

        @staticmethod
        def asColor(hexCode):
            return ColorUtils.Color.fromHEX(hexCode)

        @staticmethod
        def asTime(timeAsString):
            return TimeUtils.Time.createFromString(timeAsString)
        
        @staticmethod
        def asXY(XandY):
            found = StringUtils.Regex.findAll('\(([0-9]+), ([0-9]+)\)', XandY)
            if len(found) != 1:
                raise ExceptionUtils.ValidationError("'(X, Y)' structure is not matched.")
            return [int(found[0][0]), int(found[0][1])]

    class CommandHandler:
        
        class Generate:
            
            class OptionValidation:
                
                def SepiaTone(cfgDict):
                    pass

                def Grayscale(cfgDict):
                    pass

                def BrightnessContrast(cfgDict):
                    cfgDict['Brightness-Factor'] = Validation.asFloat(cfgDict['Brightness-Factor'])
                    cfgDict['Contrast-Factor'] = Validation.asFloat(cfgDict['Contrast-Factor'])

                def GaussianBlur(cfgDict):
                    
                    cfgDict['Kernel-Size'] = Validation.asInt(cfgDict['Kernel-Size'])
                    # ? If (...) is less or equal to 1, or is not odd. 
                    INTERNAL.Validation.Assert(cfgDict['Kernel-Size'], [
                        (lambda x: x > 1),
                        (lambda x: (x % 2) == 1),
                    ], 'Kernel size should be larger than 1, and odd.')

                def Sharpen(cfgDict):
                    cfgDict['Factor'] = Validation.asFloat(cfgDict['Factor'])

                    cfgDict['Kernel-Size'] = Validation.asInt(cfgDict['Kernel-Size'])
                    # ? If (...) is less or equal to 1, or is not odd. 
                    INTERNAL.Validation.Assert(cfgDict['Kernel-Size'], [
                        (lambda x: x > 1),
                        (lambda x: (x % 2) == 1),
                    ], 'Kernel size should be larger than 1, and odd.')

                def Pixelate(cfgDict):
                    cfgDict['Factor'] = Validation.asFloat(cfgDict['Factor'])

                def AddBorder(cfgDict):
                    cfgDict['Color'] = INTERNAL.Validation.asColor(cfgDict['Color'])
                    
                    cfgDict['Thickness'] = Validation.asInt(cfgDict['Thickness'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Thickness'], [
                        (lambda x: x > 0),
                    ], 'Thickness must be larger than 0.')

                def Crop(cfgDict):
                    cfgDict['Top-Left'] = INTERNAL.Validation.asXY(cfgDict['Top-Left'])
                    cfgDict['Bottom-Right'] = INTERNAL.Validation.asXY(cfgDict['Bottom-Right'])

                def Resize(cfgDict):
                    cfgDict['Width'] = INTERNAL.Validation.asXY(cfgDict['Width'])
                    cfgDict['Height'] = INTERNAL.Validation.asXY(cfgDict['Height'])

                def VideoFade(cfgDict):
                    cfgDict['Per-Cut'] = Validation.asBool(cfgDict['Per-Cut'])
                    
                    cfgDict['Duration'] = Validation.asInt(cfgDict['Duration'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Duration'], [
                        (lambda x: x > 0),
                    ], 'Duration must be larger than 0.')

                def AudioFade(cfgDict):
                    cfgDict['Per-Cut'] = Validation.asBool(cfgDict['Per-Cut'])
                    
                    cfgDict['Duration'] = Validation.asInt(cfgDict['Duration'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Duration'], [
                        (lambda x: x > 0),
                    ], 'Duration must be larger than 0.')

                def AudioMute(cfgDict):
                    pass

                def TrimAtKeyframes(cfgDict):
                    pass

                def GIF(cfgDict):
                    cfgDict['Capture-FPS'] = Validation.asFloat(cfgDict['Capture-FPS'])
                    cfgDict['Playback-Factor'] = Validation.asFloat(cfgDict['Playback-Factor'])
                    cfgDict['Width'] = INTERNAL.Validation.asXY(cfgDict['Width'])
                    cfgDict['Height'] = INTERNAL.Validation.asXY(cfgDict['Height'])
            
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
