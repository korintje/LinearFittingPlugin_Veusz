# -*- coding: utf-8 -*-
from veusz.plugins import ToolsPlugin, toolspluginregistry

class LinearFit(ToolsPlugin):
    """A plugin to give simple linear fit line."""
    menu = ('Linear fit',)
    name = 'Linear fit'
    description_short = 'Linear fit.'
    description_full = 'Press "Apply" to fit data.'

    def __init__(self):
        from veusz.plugins import FieldDataset
        """Construct plugin."""
        self.fields = [
            FieldDataset(
                'ds_x', descr="x dataset",
                default=''),
            FieldDataset(
                'ds_y', descr="y dataset",
                default=''),
        ]
    
    def apply(self, interface, fields):
        """
        Select and load image file from a dialog.
        All widgets in the current window will be wiped.  
        """
        import numpy as np

        xs = interface.GetData(fields["ds_x"])[0]
        ys = interface.GetData(fields["ds_y"])[0]
        
        coefs = np.polynomial.polynomial.polyfit(xs, ys, 1, full=False)
        b = coefs[0]
        a = coefs[1]
        root = interface.Root
        page = root.Add('page')
        graph = page.Add('graph')
        line = graph.Add('function', function=f'{a} * x + {b}')

# add the class to the registry.
toolspluginregistry.append(LinearFit)



