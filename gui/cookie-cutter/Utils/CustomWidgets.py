
import automatey.GUI.GElements as GElements
import automatey.GUI.GConcurrency as GConcurrency
import automatey.GUI.GUtils as GUtils

class FilterOptions:

    class SepiaTone(GElements.Widgets.Complex.FilterList.FilterOption):
        
        def __init__(self):
            self.null = GElements.Widgets.Basics.Null(size=[50, 50])
            super().__init__(self.null)
            
        def getData(self):
            return {
                'name' : __class__.getName()
            }
        
        @staticmethod
        def getName():
            return 'Sepia Tone'

    class GrayScale(GElements.Widgets.Complex.FilterList.FilterOption):
        
        def __init__(self):
            self.null = GElements.Widgets.Basics.Null(size=[50, 50])
            super().__init__(self.null)
            
        def getData(self):
            return {
                'name' : __class__.getName()
            }
        
        @staticmethod
        def getName():
            return 'Gray Scale'
