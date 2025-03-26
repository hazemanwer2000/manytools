
import automatey.GUI.GConcurrency as GConcurrency
import automatey.OS.FileUtils as FileUtils
import automatey.Media.VideoUtils as VideoUtils
import automatey.OS.ProcessUtils as ProcessUtils
import automatey.Utils.ColorUtils as ColorUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.Utils.TimeUtils as TimeUtils
import automatey.Utils.ExceptionUtils as ExceptionUtils
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
    
    Constants = {
        'Default-CRF' : 17,
    }
    
    # ? Video-handler.
    video:VideoUtils.Video = None

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
            found = StringUtils.Regex.findAll('(-?[0-9]+),[ ]*(-?[0-9]+)', XandY)
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

                def Brightness(cfgDict):
                    cfgDict['Brightness-Factor'] = Validation.asFloat(cfgDict['Brightness-Factor'])
                    cfgDict['Contrast-Factor'] = Validation.asFloat(cfgDict['Contrast-Factor'])
                    cfgDict['Saturation-Factor'] = Validation.asFloat(cfgDict['Saturation-Factor'])

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
                    cfgDict['Factor'] = Validation.asInt(cfgDict['Factor'])
                    # ? If (...) is less than 1. 
                    INTERNAL.Validation.Assert(cfgDict['Factor'], [
                        (lambda x: x >= 1),
                    ], 'Factor must be larger or equal to 1.')

                def Noise(cfgDict):
                    cfgDict['Factor'] = Validation.asFloat(cfgDict['Factor'])
                    # ? If (...) is less than 1. 
                    INTERNAL.Validation.Assert(cfgDict['Factor'], [
                        (lambda x: x >= 1),
                    ], 'Factor must be larger or equal to 1.')

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
                    
                    cfgDict['Width'] = Validation.asInt(cfgDict['Width'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Width'], [
                        (lambda x: (x > 0) or (x == -1)),
                    ], 'Dimension must be larger than 0, or -1.')
                    
                    cfgDict['Height'] = Validation.asInt(cfgDict['Height'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Height'], [
                        (lambda x: (x > 0) or (x == -1)),
                    ], 'Dimension must be larger than 0, or -1.')

                def Rotate(cfgDict):
                    cfgDict['Angle'] = Validation.asInt(cfgDict['Angle'])
                                
                def Mirror(cfgDict):
                    pass

                def VideoFade(cfgDict):
                    cfgDict['Per-Cut'] = Validation.asBool(cfgDict['Per-Cut'])
                    
                    cfgDict['Duration'] = Validation.asFloat(cfgDict['Duration'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Duration'], [
                        (lambda x: x > 0),
                    ], 'Duration must be larger than 0.')

                def AudioFade(cfgDict):
                    cfgDict['Per-Cut'] = Validation.asBool(cfgDict['Per-Cut'])
                    
                    cfgDict['Duration'] = Validation.asFloat(cfgDict['Duration'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Duration'], [
                        (lambda x: x > 0),
                    ], 'Duration must be larger than 0.')

                def CRF(cfgDict):
                    cfgDict['Value'] = Validation.asInt(cfgDict['Value'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Value'], [
                        (lambda x: x > 0),
                    ], 'CRF must be larger than 0.')

                def AudioMute(cfgDict):
                    pass

                def TrimAtKeyframes(cfgDict):
                    pass

                def GIF(cfgDict):
                    cfgDict['Capture-FPS'] = Validation.asFloat(cfgDict['Capture-FPS'])
                    cfgDict['Playback-Factor'] = Validation.asFloat(cfgDict['Playback-Factor'])
                    
                    cfgDict['Width'] = Validation.asInt(cfgDict['Width'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Width'], [
                        (lambda x: (x > 0) or (x == -1)),
                    ], 'Dimension must be larger than 0, or -1.')
                    
                    cfgDict['Height'] = Validation.asInt(cfgDict['Height'])
                    # ? (...)
                    INTERNAL.Validation.Assert(cfgDict['Height'], [
                        (lambda x: (x > 0) or (x == -1)),
                    ], 'Dimension must be larger than 0, or -1.')
            
            class OptionProcess:
                
                def SepiaTone(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.SepiaTone())

                def Grayscale(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Grayscale())

                def Brightness(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Brightness(brightness=cfgDict['Brightness-Factor'],
                                                                                                        contrast=cfgDict['Contrast-Factor'],
                                                                                                        saturation=cfgDict['Saturation-Factor']))

                def GaussianBlur(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.GaussianBlur(kernelSize=cfgDict['Kernel-Size']))

                def Sharpen(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Sharpen(factor=cfgDict['Factor'],
                                                                                         kernelSize=cfgDict['Kernel-Size']))

                def Pixelate(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Pixelate(factor=cfgDict['Factor']))

                def Noise(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Noise(factor=cfgDict['Factor']))

                def AddBorder(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.AddBorder(AbstractGraphics.Border(thickness=cfgDict['Thickness'],
                                                                                                                   color=cfgDict['Color'])))

                def Crop(cfgDict, struct):
                    topLeft = AbstractGraphics.Point(cfgDict['Top-Left'][0], cfgDict['Top-Left'][1])
                    bottomRight = AbstractGraphics.Point(cfgDict['Bottom-Right'][0], cfgDict['Bottom-Right'][1])
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Crop(topLeft=topLeft, bottomRight=bottomRight))

                def Resize(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Filters.Resize(cfgDict['Width'], cfgDict['Height']))

                def Rotate(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Transformations.Rotate(AbstractGraphics.Rotation(cfgDict['Angle'])))

                Mirror2Mirror = {
                    'Horizontal' : AbstractGraphics.Mirror.Horizontal,
                    'Vertical' : AbstractGraphics.Mirror.Vertical,
                }

                def Mirror(cfgDict, struct):
                    struct['filters']['general'].append(VideoUtils.Modifiers.Transformations.Mirror(
                        INTERNAL.CommandHandler.Generate.OptionProcess.Mirror2Mirror[cfgDict['Direction']]
                    ))

                def VideoFade(cfgDict, struct):
                    fadeInModifier = VideoUtils.Modifiers.Transitions.FadeIn(TimeUtils.Time.createFromSeconds(cfgDict['Duration']))
                    fadeOutModifier = VideoUtils.Modifiers.Transitions.FadeOut(TimeUtils.Time.createFromSeconds(cfgDict['Duration']))
                    if cfgDict['Per-Cut'] == True:
                        struct['filters']['general'].append(fadeInModifier)
                        struct['filters']['general'].append(fadeOutModifier)
                    else:
                        struct['filters']['first-cut-only'].append(fadeInModifier)
                        struct['filters']['last-cut-only'].append(fadeOutModifier)

                def AudioFade(cfgDict, struct):
                    fadeInModifier = VideoUtils.AudioModifiers.Transitions.FadeIn(TimeUtils.Time.createFromSeconds(cfgDict['Duration']))
                    fadeOutModifier = VideoUtils.AudioModifiers.Transitions.FadeOut(TimeUtils.Time.createFromSeconds(cfgDict['Duration']))
                    if cfgDict['Per-Cut'] == True:
                        struct['filters']['general'].append(fadeInModifier)
                        struct['filters']['general'].append(fadeOutModifier)
                    else:
                        struct['filters']['first-cut-only'].append(fadeInModifier)
                        struct['filters']['last-cut-only'].append(fadeOutModifier)

                def CRF(cfgDict, struct):
                    struct['CRF'] = cfgDict['Value']

                def AudioMute(cfgDict, struct):
                    struct['is-mute'] = True

                def TrimAtKeyframes(cfgDict, struct):
                    struct['is-nearest-keyframe'] = True

                def GIF(cfgDict, struct):
                    struct['gif-action'] = VideoUtils.Actions.GIF(
                        captureFPS=cfgDict['Capture-FPS'],
                        playbackFactor=cfgDict['Playback-Factor'],
                        width=cfgDict['Width'],
                        height=cfgDict['Height'],
                    )
            
            @staticmethod
            def runner(commandStruct):
                
                resultStatus = 0
                resultInfo = ''
                
                try:
                    
                    # ? Clean-up arguments.
                    
                    # ? ? Process time-entries.
                    for trimTimeEntry in commandStruct['Trim-Times']:
                        
                        if trimTimeEntry['Start-Time'] != '':
                            trimTimeEntry['Start-Time'] = INTERNAL.Validation.asTime(trimTimeEntry['Start-Time'])
                        else:
                            trimTimeEntry['Start-Time'] = None
                            
                        if trimTimeEntry['End-Time'] != '':
                            trimTimeEntry['End-Time'] = INTERNAL.Validation.asTime(trimTimeEntry['End-Time'])
                        else:
                            trimTimeEntry['End-Time'] = None
                    
                    # ? ? Options.
                    for option in commandStruct['Options']:
                        INTERNAL.CommandHandler.Generate.OptionValidation.__dict__[option['Name'].replace('-', '')](option['Cfg'])
                        
                    # ? Process arguments.
                    
                    # ? ? Process option(s).
                    struct = {
                        'is-mute' : False,
                        'is-nearest-keyframe' : False,
                        'filters' : {
                            'general' : [],
                            'first-cut-only' : [],
                            'last-cut-only' : [],
                        },
                        'gif-action' : None,
                        'CRF' : INTERNAL.Constants['Default-CRF'],
                    }
                    for option in commandStruct['Options']:
                        INTERNAL.CommandHandler.Generate.OptionProcess.__dict__[option['Name'].replace('-', '')](option['Cfg'], struct)
                    
                    # ? ? ? Fix: Because micro-seconds are neglected by the video-player, must increment by 1-ms when exporting by finding nearest (previous) key-frame.
                    if struct['is-nearest-keyframe']:
                        for trimTimeEntry in commandStruct['Trim-Times']:
                            if not (trimTimeEntry['Start-Time'] is None):
                                trimTimeEntry['Start-Time'] = trimTimeEntry['Start-Time'] + TimeUtils.Time.createFromMilliseconds(50)
                    
                    # ? ? Setup Trim action(s).
                    trimActions = []
                    for idx, trimTimeEntry in enumerate(commandStruct['Trim-Times']):
                        
                        # ? ? ? Pick-out filter(s).
                        filters = []
                        filters.extend(struct['filters']['general'])
                        if idx == 0:
                            filters.extend(struct['filters']['first-cut-only'])
                        if idx == (len(commandStruct['Trim-Times']) - 1):
                            filters.extend(struct['filters']['last-cut-only'])
                        
                        # ? ? ? (...)
                        trimAction = VideoUtils.Actions.Trim(trimTimeEntry['Start-Time'], 
                                                             trimTimeEntry['End-Time'], 
                                                             isMute=struct['is-mute'],
                                                             isNearestKeyframe=struct['is-nearest-keyframe'],
                                                             modifiers=filters,
                                                             CRF=struct['CRF'])
                        trimActions.append(trimAction)
                    
                    # ? ? Other action(s) (...)
                    
                    joinAction = VideoUtils.Actions.Join(*trimActions)
                    INTERNAL.video.registerAction(joinAction)

                    if not (struct['gif-action'] is None):
                        INTERNAL.video.registerAction(struct['gif-action'])    
                    
                    # ? ? Generate.
                    
                    if not (struct['gif-action'] is None):
                        ext_dst = 'gif'
                    elif not struct['is-nearest-keyframe']:
                        ext_dst = 'mp4'
                    else:
                        ext_dst = None

                    f_dst = FileUtils.File(FileUtils.File.Utils.Path.iterateName(
                        FileUtils.File.Utils.Path.modifyName(str(INTERNAL.Parameters.f_video), extension=ext_dst)
                    ))
                    INTERNAL.video.saveAs(f_dst)
                    INTERNAL.video.clearActions()
                
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
        f_video:FileUtils.File = None
        f_videoInfoTemplate = None

    @staticmethod
    def longInitialize():
        
        # ? (Long-)Initialization, takes place at the start of the infinite loop.
        INTERNAL.video = VideoUtils.Video(INTERNAL.Parameters.f_video)
        
        # ? Initialization of video information.
        VideoInformation.keyframes = INTERNAL.video.getKeyframes()
        VideoInformation.fps = INTERNAL.video.getFPS()
        VideoInformation.dimensions = INTERNAL.video.getDimensions()
        VideoInformation.duration = INTERNAL.video.getDuration()
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
