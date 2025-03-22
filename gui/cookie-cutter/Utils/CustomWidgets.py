
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.Utils.ColorUtils as ColorUtils

import collections

class FilterOption(GElements.Widgets.Complex.FilterList.FilterOption):

    def getData(self):
        return {
            'Name' : self.getName(),
            'Cfg' : {},
        }

class FilterOptionLess(FilterOption):
    '''
    For option(s) with no cfg. param.
    '''
    
    def __init__(self):
        self.label = GElements.Widgets.Basics.Label(self.getName())
        super().__init__(self.label)

class FilterOptionFull(FilterOption):
    '''
    For option(s) with one or more cfg. param.
    '''

    def __init__(self, cfgNames:list, cfgWidgets:list):
        
        # ? Setup option's title and container.
        self.rootTitleLabel = GElements.Widgets.Basics.Label(self.getName()) 
        self.rootVerticalContainer = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
        self.rootVerticalContainer.getLayout().insertWidget(self.rootTitleLabel)
        
        # ? For each cfg. param, setup a label (...), then add it to (root-)container.
        self.cfgLabels = []
        for cfgName, cfgWidget in zip(cfgNames, cfgWidgets):
            cfgLabel = GElements.Widgets.Basics.Label(cfgName)
            cfgVerticalContainer = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
            cfgVerticalContainer.getLayout().insertWidget(cfgLabel)
            cfgVerticalContainer.getLayout().insertWidget(cfgWidget)
            self.rootVerticalContainer.getLayout().insertWidget(GElements.Widgets.Decorators.Outline(cfgVerticalContainer,
                                                                                                     elementMargin=AbstractGraphics.SymmetricMargin(5)))
        
        self.cfgWidgets = cfgWidgets
        self.cfgNames = cfgNames
        
        super().__init__(self.rootVerticalContainer)
    
    def getData(self):
        dataDict = super().getData()
        for cfgName, cfgWidget in zip(self.cfgNames, self.cfgWidgets):
            dataDict['Cfg'][cfgName] = str(cfgWidget).strip()
        return dataDict

class FilterOptions:

    class SepiaTone(FilterOptionLess):
        pass
            
    class Grayscale(FilterOptionLess):
        pass

    class Brightness(FilterOptionFull):
        
        def __init__(self):
            cfgNames = [
                'Brightness-Factor',
                'Contrast-Factor',
                'Saturation-Factor',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class GaussianBlur(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Kernel-Size',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 3, 5, 7'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Sharpen(FilterOptionFull):
        
        def __init__(self):
            cfgNames = [
                'Factor',
                'Kernel-Size',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 3, 5, 7'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Pixelate(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Factor',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 2, 4, 8'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Noise(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Factor',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class AddBorder(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Thickness',
                'Color',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 50'),
                GElements.Widgets.Complex.ColorSelector(ColorUtils.Colors.BLACK),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Crop(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Top-Left',
                'Bottom-Right',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., (1, 1), (W, H)"),
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., (1, 1), (W, H)"),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Resize(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Width',
                'Height',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., 600, -1 (i.e., auto)"),
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., 400, -1 (i.e., auto)"),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Rotate(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Angle',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., 90, -90, 180"),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class Mirror(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Direction',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.DropDownList(['Vertical', 'Horizontal'])
            ]
            super().__init__(cfgNames, cfgWidgets)

    class VideoFade(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Duration',
                'Per-Cut',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="i.e., in seconds"),
                GElements.Widgets.Basics.CheckBox(),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class AudioFade(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Duration',
                'Per-Cut',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="i.e., in seconds"),
                GElements.Widgets.Basics.CheckBox(),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class CRF(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Value',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder='i.e., 12, 15, 17, 20'),
            ]
            super().__init__(cfgNames, cfgWidgets)

    class AudioMute(FilterOptionLess):
        pass

    class TrimAtKeyframes(FilterOptionLess):
        pass

    class GIF(FilterOptionFull):

        def __init__(self):
            cfgNames = [
                'Capture-FPS',
                'Playback-Factor',
                'Width',
                'Height',
            ]
            cfgWidgets = [
                GElements.Widgets.Basics.LineEdit(placeholder="i.e., 10"),
                GElements.Widgets.Basics.LineEdit(placeholder='e.g., 1.0 has no effect'),
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., 600, -1 (i.e., auto)"),
                GElements.Widgets.Basics.LineEdit(placeholder="e.g., 400, -1 (i.e., auto)"),
            ]
            super().__init__(cfgNames, cfgWidgets)
