
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils
import automatey.Abstract.Graphics as AbstractGraphics
import automatey.Base.ColorUtils as ColorUtils

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
    
    def __init__(self, cfgNames:list, cfgPlaceholders:list):
        
        # ? Setup option's title and container.
        self.rootTitleLabel = GElements.Widgets.Basics.Label(self.getName()) 
        self.rootVerticalContainer = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
        self.rootVerticalContainer.getLayout().insertWidget(self.rootTitleLabel)
        
        # ? For each cfg. param, setup a label, and a line-edit, then add it to (root-)container.
        self.cfgLabels = []
        self.cfgLineEdits = []
        for cfgName, cfgPlaceholder in zip(cfgNames, cfgPlaceholders):
            cfgLabel = GElements.Widgets.Basics.Label(cfgName)
            cfgLineEdit = GElements.Widgets.Basics.LineEdit(placeholder=cfgPlaceholder)
            cfgVerticalContainer = GElements.Widgets.Containers.VerticalContainer(elementMargin=AbstractGraphics.SymmetricMargin(0), elementSpacing=5)
            cfgVerticalContainer.getLayout().insertWidget(cfgLabel)
            cfgVerticalContainer.getLayout().insertWidget(GElements.Widgets.Decorators.Outline(cfgLineEdit,
                                                                                               elementMargin=AbstractGraphics.SymmetricMargin(5)))
            self.rootVerticalContainer.getLayout().insertWidget(GElements.Widgets.Decorators.Outline(cfgVerticalContainer,
                                                                                                     elementMargin=AbstractGraphics.SymmetricMargin(5)))
        
        super().__init__(self.rootVerticalContainer)

class FilterOptions:

    class SepiaTone(FilterOptionLess):
        pass
            
    class Grayscale(FilterOptionLess):
        pass

    class BrightnessContrast(FilterOptionFull):
        
        def __init__(self):
            self.cfgNames = [
                'Brightness-Factor',
                'Contrast-Factor',
            ]
            self.cfgPlaceholders = [
                '(e.g., 1.0 has no effect)',
                '(e.g., 1.0 has no effect)',
            ]
            super().__init__(self.cfgNames, self.cfgPlaceholders)

