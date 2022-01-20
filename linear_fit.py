# -*- coding: utf-8 -*-
from veusz.plugins import importpluginregistry, ImportPlugin

class ImportSPA(ImportPlugin):
    """A plugin for reading Thermo Scientific OMNIC SPA file."""
    name = 'OMNIC SPA import'
    author = 'Takuro Hosomi'
    description = 'Read a spectrum from Thermo Scientific OMNIC SPA file'
    file_extensions = set(['.spa', '.SPA'])

    def __init__(self):
        from veusz.plugins import ImportPlugin, ImportFieldText
        ImportPlugin.__init__(self)
        self.fields = [
            ImportFieldText("x_name", descr="X-axis name", default="wavenumber"),
            ImportFieldText("y_name", descr="Y-axis name", default=r"{auto}")
        ]
    
    def doImport(self, params):
        """Actually import data"""
        import numpy as np
        from veusz.plugins import ImportDataset1D, ImportPluginException

        class SPAData():

            def __init__(self, filepath):
                self.datanum = 1
                self.title = ""
                self.max_wavenum = 0
                self.min_wavenum = 0
                self.wavenumbers = np.zeros(1)
                self.data = np.zeros(1)
                self.loadfromFile(filepath)
            
            def loadfromFile(self, filepath):
                with open(filepath, 'rb') as f:
                    # Get spectrum title
                    f.seek(30)
                    title = np.fromfile(f, np.uint8,255)
                    self.title = ''.join([chr(x) for x in title if x!=0])

                    # Get number of datapoints in wavenumber array
                    f.seek(564)
                    self.datanum = np.fromfile(f, np.int32,1)[0]
                    
                    # Get wavenumber array
                    f.seek(576)
                    self.max_wavenum = np.fromfile(f, np.single, 1)[0]
                    self.min_wavenum = np.fromfile(f, np.single, 1)[0]
                    self.wavenumbers = np.linspace(self.max_wavenum, self.min_wavenum, self.datanum)

                    # Search and move start address of data
                    f.seek(288)
                    flag = 0
                    while flag != 3:
                        flag = np.fromfile(f, np.uint16, 1)
                    data_position=np.fromfile(f,np.uint16, 1)[0]
                    f.seek(data_position)

                    # Get spectrum data
                    self.data = np.fromfile(f, np.single, self.datanum)

        try:
            self.spadata = SPAData(params.filename)
            x_name = params.field_results["x_name"]
            y_name = params.field_results["y_name"]
            if y_name == r"{auto}":
                y_name = self.spadata.title
            return [
                ImportDataset1D(x_name, self.spadata.wavenumbers),
                ImportDataset1D(y_name, self.spadata.data),
            ]
        except IOError as e:
            raise e
        except Exception as e:
            raise ImportPluginException(str(e))

# add the class to the registry.
importpluginregistry.append(ImportSPA)



class WidgetsClone(ToolsPlugin):
    """Take a widget and children and clone them."""

    menu = (_('Widgets'), _('Clone for datasets'))
    name = 'Clone widgets for datasets'
    description_short = _('Clones a widget and its children for datasets')
    description_full = _('Take a widget and its children and clone it, plotting different sets of data in each clone.\nHint: Use a "*" in the name of a replacement dataset to match multiple datasets, e.g. x_*')

    def __init__(self):
        """Construct plugin."""
        self.fields = [
            field.FieldWidget(
                "widget", descr=_("Clone widget"),
                default=""),
            field.FieldDataset(
                'ds1', descr=_("Dataset 1 to change"),
                default=''),
            field.FieldDatasetMulti(
                'ds1repl',
                descr=_("Replacement(s) for dataset 1")),
            field.FieldDataset(
                'ds2', descr=_("Dataset 2 to change (optional)"),
                default=''),
            field.FieldDatasetMulti(
                'ds2repl',
                descr=_("Replacement(s) for dataset 2")),
            field.FieldBool(
                "names", descr=_("Build new names from datasets"),
                default=True),
        ]

    def apply(self, ifc, fields):
        """Do the cloning."""

        def expanddatasets(dslist):
            """Expand * and ? in dataset names."""
            datasets = []
            for ds in dslist:
                if ds.find('*') == -1 and ds.find('?') == -1:
                    datasets.append(ds)
                else:
                    dlist = fnmatch.filter(ifc.GetDatasets(), ds)
                    dlist.sort()
                    datasets += dlist
            return datasets

        def chainpairs(dslist1, dslist2):
            """Return pairs of datasets, repeating if necessary."""
            if not dslist1:
                dslist1 = ['']
            if not dslist2:
                dslist2 = ['']

            end1 = end2 = False
            idx1 = idx2 = 0
            while True:
                if idx1 >= len(ds1repl):
                    idx1 = 0
                    end1 = True
                if idx2 >= len(ds2repl):
                    idx2 = 0
                    end2 = True
                if end1 and end2:
                    break

                yield dslist1[idx1], dslist2[idx2]
                idx1 += 1
                idx2 += 1

        def walkNodes(node, dsname, dsrepl):
            """Walk nodes, changing datasets."""
            if node.type == 'setting':
                if node.settingtype in (
                        'dataset', 'dataset-extended',
                        'dataset-or-floatlist', 'dataset-or-str'):
                    # handle single datasets
                    if node.val == dsname:
                        node.val = dsrepl
                elif node.settingtype == 'dataset-multi':
                    # settings with multiple datasets
                    out = list(node.val)
                    for i, v in enumerate(out):
                        if v == dsname:
                            out[i] = dsrepl
                    if tuple(out) != node.val:
                        node.val = out
            else:
                for c in node.children:
                    walkNodes(c, dsname, dsrepl)

        # get names of replacement datasets
        ds1repl = expanddatasets(fields['ds1repl'])
        ds2repl = expanddatasets(fields['ds2repl'])

        # make copies of widget and children for each pair of datasets
        widget = ifc.Root.fromPath(fields['widget'])
        for ds1r, ds2r in chainpairs(ds1repl, ds2repl):
            # construct a name
            newname = None
            if fields['names']:
                newname = widget.name
                if ds1r:
                    # / cannot be in dataset name
                    flt1 = ds1r.replace('/', '_')
                    newname += ' ' + flt1
                if ds2r:
                    flt2 = ds2r.replace('/', '_')
                    newname += ' ' + flt2

            # make the new widget (and children)
            newwidget = widget.Clone(widget.parent, newname=newname)

            # do replacement of datasets
            if fields['ds1']:
                walkNodes(newwidget, fields['ds1'], ds1r)
            if fields['ds2']:
                walkNodes(newwidget, fields['ds2'], ds2r)class WidgetsClone(ToolsPlugin):
    """Take a widget and children and clone them."""

    menu = (_('Widgets'), _('Clone for datasets'))
    name = 'Clone widgets for datasets'
    description_short = _('Clones a widget and its children for datasets')
    description_full = _('Take a widget and its children and clone it, plotting different sets of data in each clone.\nHint: Use a "*" in the name of a replacement dataset to match multiple datasets, e.g. x_*')

    def __init__(self):
        """Construct plugin."""
        self.fields = [
            field.FieldWidget(
                "widget", descr=_("Clone widget"),
                default=""),
            field.FieldDataset(
                'ds1', descr=_("Dataset 1 to change"),
                default=''),
            field.FieldDatasetMulti(
                'ds1repl',
                descr=_("Replacement(s) for dataset 1")),
            field.FieldDataset(
                'ds2', descr=_("Dataset 2 to change (optional)"),
                default=''),
            field.FieldDatasetMulti(
                'ds2repl',
                descr=_("Replacement(s) for dataset 2")),
            field.FieldBool(
                "names", descr=_("Build new names from datasets"),
                default=True),
        ]

    def apply(self, ifc, fields):
        """Do the cloning."""

        def expanddatasets(dslist):
            """Expand * and ? in dataset names."""
            datasets = []
            for ds in dslist:
                if ds.find('*') == -1 and ds.find('?') == -1:
                    datasets.append(ds)
                else:
                    dlist = fnmatch.filter(ifc.GetDatasets(), ds)
                    dlist.sort()
                    datasets += dlist
            return datasets

        def chainpairs(dslist1, dslist2):
            """Return pairs of datasets, repeating if necessary."""
            if not dslist1:
                dslist1 = ['']
            if not dslist2:
                dslist2 = ['']

            end1 = end2 = False
            idx1 = idx2 = 0
            while True:
                if idx1 >= len(ds1repl):
                    idx1 = 0
                    end1 = True
                if idx2 >= len(ds2repl):
                    idx2 = 0
                    end2 = True
                if end1 and end2:
                    break

                yield dslist1[idx1], dslist2[idx2]
                idx1 += 1
                idx2 += 1

        def walkNodes(node, dsname, dsrepl):
            """Walk nodes, changing datasets."""
            if node.type == 'setting':
                if node.settingtype in (
                        'dataset', 'dataset-extended',
                        'dataset-or-floatlist', 'dataset-or-str'):
                    # handle single datasets
                    if node.val == dsname:
                        node.val = dsrepl
                elif node.settingtype == 'dataset-multi':
                    # settings with multiple datasets
                    out = list(node.val)
                    for i, v in enumerate(out):
                        if v == dsname:
                            out[i] = dsrepl
                    if tuple(out) != node.val:
                        node.val = out
            else:
                for c in node.children:
                    walkNodes(c, dsname, dsrepl)

        # get names of replacement datasets
        ds1repl = expanddatasets(fields['ds1repl'])
        ds2repl = expanddatasets(fields['ds2repl'])

        # make copies of widget and children for each pair of datasets
        widget = ifc.Root.fromPath(fields['widget'])
        for ds1r, ds2r in chainpairs(ds1repl, ds2repl):
            # construct a name
            newname = None
            if fields['names']:
                newname = widget.name
                if ds1r:
                    # / cannot be in dataset name
                    flt1 = ds1r.replace('/', '_')
                    newname += ' ' + flt1
                if ds2r:
                    flt2 = ds2r.replace('/', '_')
                    newname += ' ' + flt2

            # make the new widget (and children)
            newwidget = widget.Clone(widget.parent, newname=newname)

            # do replacement of datasets
            if fields['ds1']:
                walkNodes(newwidget, fields['ds1'], ds1r)
            if fields['ds2']:
                walkNodes(newwidget, fields['ds2'], ds2r)
