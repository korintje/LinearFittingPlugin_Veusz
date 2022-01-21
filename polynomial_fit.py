# -*- coding: utf-8 -*-
# Written by Takuro Hosomi
# The script license is copy-lefted from Veusz to be GPL v2.0

from veusz.plugins import ToolsPlugin, toolspluginregistry

class LinearFit(ToolsPlugin):
    """A plugin to do polynomial fit """
    menu = ('Polynomial fit',)
    name = 'Polynomial fit'
    description_short = 'Do polynomial fit.'
    description_full = 'Press "Apply" to fit data.'

    def __init__(self):
        from veusz.plugins import FieldDataset, FieldInt
        """Construct plugin."""
        self.fields = [
            FieldInt(
                'dim', descr='dimension',
                default=1),
            FieldDataset(
                'xs_name', descr='x dataset',
                default=''),
            FieldDataset(
                'ys_name', descr='y dataset',
                default=''),
        ]
    
    def apply(self, interface, fields):
        """
        Function of fitting result will be added.  
        """
        import numpy as np

        dim = fields['dim']
        xs = interface.GetData(fields['xs_name'])[0]
        ys = interface.GetData(fields['ys_name'])[0]
        
        coeffs = np.polynomial.polynomial.polyfit(xs, ys, dim, full=False)
        expr = ''
        for i, coeff in enumerate(coeffs):
            if i == 0:
                expr += f'{coeff}'
            else:
                expr += f' + {coeff} * x**{i}'
        root = interface.Root
        page = root.Add('page')
        graph = page.Add('graph')
        line = graph.Add('function', function=expr)

# add the class to the registry.
toolspluginregistry.append(LinearFit)
