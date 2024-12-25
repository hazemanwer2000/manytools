
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.Base.ColorUtils as ColorUtils

import collections

class FilterOption(GElements.Widgets.Complex.FilterList.FilterOption):

    def getData(self):
        return {
            'Name' : __class__.getName()
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
        
        super().__init__(self.rootVerticalContainer)

class FilterOptionLineEditOnly(FilterOptionFull):
    '''
    For option(s) with line-input only.
    '''
    
    def __init__(self, cfgNames:list, cfgPlaceholders:list):
        self.cfgLineEdits = []
        for cfgPlaceholder in cfgPlaceholders:
            cfgLineEdit = GElements.Widgets.Basics.LineEdit(placeholder=cfgPlaceholder)
            self.cfgLineEdits.append(cfgLineEdit)
        super().__init__(cfgNames, self.cfgLineEdits)

class FilterOptions:

    class SepiaTone(FilterOptionLess):
        pass
            
    class Grayscale(FilterOptionLess):
        pass

    class BrightnessContrast(FilterOptionLineEditOnly):
        
        def __init__(self):
            self.cfgNames = [
                'Brightness-Factor',
                'Contrast-Factor',
            ]
            self.cfgPlaceholders = [
                'e.g., 1.0 has no effect',
                'e.g., 1.0 has no effect',
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class GaussianBlur(FilterOptionLineEditOnly):
        
        def __init__(self):
            self.cfgNames = [
                'Kernel-Size',
            ]
            self.cfgPlaceholders = [
                'e.g., 3, 5, 7',
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class Sharpen(FilterOptionLineEditOnly):
        
        def __init__(self):
            self.cfgNames = [
                'Factor',
                'Kernel-Size',
            ]
            self.cfgPlaceholders = [
                'e.g., 1.0 has no effect',
                'e.g., 3, 5, 7',
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class Pixelate(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Factor',
            ]
            self.cfgPlaceholders = [
                'e.g., 1.0 has no effect',
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class AddBorder(FilterOptionFull):

        def __init__(self):
            
            self.cfgName2Widget = collections.OrderedDict()
            self.cfgName2Widget['Thickness'] = GElements.Widgets.Basics.LineEdit(placeholder='e.g., 50')
            self.cfgName2Widget['Color'] = GElements.Widgets.Complex.ColorSelector(ColorUtils.Colors.BLACK)
            
            super().__init__(self.cfgName2Widget.keys(), self.cfgName2Widget.values())

    class Crop(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Top-Left',
                'Bottom-Right',
            ]
            self.cfgPlaceholders = [
                "e.g., (1, 1), (W, H)",
                "e.g., (1, 1), (W, H)",
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class Resize(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Width',
                'Height',
            ]
            self.cfgPlaceholders = [
                "e.g., 600, -1 (i.e., keep aspect ratio)",
                "e.g., 400, -1 (i.e., keep aspect ratio)",
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class VideoFade(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Duration',
                'Per-Cut',
            ]
            self.cfgPlaceholders = [
                "i.e., in seconds",
                "i.e., yes or no",
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class AudioFade(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Duration',
                'Per-Cut',
            ]
            self.cfgPlaceholders = [
                "i.e., in seconds",
                "i.e., yes or no",
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

    class AudioMute(FilterOptionLess):
        pass

    class GIF(FilterOptionLineEditOnly):

        def __init__(self):
            self.cfgNames = [
                'Capture-FPS',
                'Playback-Factor',
                'Width',
                'Height',
            ]
            self.cfgPlaceholders = [
                "i.e., 10",
                'e.g., 1.0 has no effect',
                "e.g., 600, -1 (i.e., keep aspect ratio)",
                "e.g., 400, -1 (i.e., keep aspect ratio)",
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)
