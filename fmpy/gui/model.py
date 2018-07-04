from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QPixmap, QFont

from ..model_description import ScalarVariable


class TreeItem(object):

    def __init__(self, name=None, variable=None):
        self.parent = None
        self.name = name
        self.variable = variable
        self.children = []

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def addChild(self, child):
        i = 0
        for i, sibling in enumerate(self.children):
            if sibling.name.upper() > child.name.upper():
                break
        self.children.insert(i, child)
        child.parent = self


class VariablesModel(QAbstractItemModel):

    COLUMN_NAMES = ['Name', 'Value Reference', 'Initial', 'Causality', 'Variability', 'Start', 'Unit', 'Plot', 'Description']
    COLUMN_WIDTHS = [200, 100, 70, 70, 70, 70, 40, 40]
    variableSelected = pyqtSignal(ScalarVariable, name='variableSelected')
    variableDeselected = pyqtSignal(ScalarVariable, name='variableDeselected')

    def __init__(self, selectedVariables, startValues, parent=None):
        super(VariablesModel, self).__init__(parent)
        self.selectedVariables = selectedVariables
        self.startValues = startValues
        self.modelDescription = None
        self.boldFont = QFont()
        self.boldFont.setBold(True)

    def columnCount(self, parent):
        return len(self.COLUMN_NAMES)

    def headerData(self, col, orientation, role):

        if role == Qt.DisplayRole:
            return self.COLUMN_NAMES[col]

        return None

    def columnData(self, v, column, role):

        if role == Qt.DecorationRole and column == 'Name':
            if v.causality in ['input', 'output']:
                return QPixmap(':/icons/%s_%s.png' % (v.type.lower(), v.causality))
            else:
                return QPixmap(':/icons/%s.png' % v.type.lower())

        elif role == Qt.CheckStateRole and column == 'Plot':
            return Qt.Checked if v in self.selectedVariables else Qt.Unchecked

        elif role == Qt.TextAlignmentRole and column in ['Value Reference', 'Start']:
            return Qt.AlignRight | Qt.AlignVCenter

        elif role == Qt.FontRole and column == 'Start' and v.name in self.startValues:
            return self.boldFont

        elif role == Qt.DisplayRole or role == Qt.EditRole:
            if column == 'Name':
                return v.name
            elif column == 'Value Reference':
                return v.valueReference
            elif column == 'Initial':
                return v.initial
            elif column == 'Causality':
                return v.causality
            elif column == 'Variability':
                return v.variability
            elif column == 'Start':
                if v.name in self.startValues:
                    return self.startValues[v.name]
                elif v.start is not None:
                    return str(v.start)
            elif column == 'Unit':
                if v.unit is not None:
                    return v.unit
                elif v.declaredType is not None and v.declaredType.unit is not None:
                    return v.declaredType.unit
            elif column == 'Description':
                return v.description

        return None

    def flags(self, index):

        if not index.isValid():
            return 0

        column = self.COLUMN_NAMES[index.column()]

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if column == 'Plot':
            flags |= Qt.ItemIsUserCheckable
        elif column == 'Start':
            flags |= Qt.ItemIsEditable

        return flags

    def setData(self, index, value, role):

        if not index.isValid():
            return False

        variable = self.variableForIndex(index)
        column = self.COLUMN_NAMES[index.column()]

        if column == 'Start':
            if value:
                self.startValues[variable.name] = value
            else:
                self.startValues.pop(variable.name, None)
            return True
        elif column == 'Plot' and role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.variableSelected.emit(variable)
            else:
                self.variableDeselected.emit(variable)
            return True

        return False

    def variableForIndex(self, index):
        raise NotImplementedError()


class VariablesTableModel(VariablesModel):

    def __init__(self, selectedVariables, startValues, parent=None):
        super(VariablesTableModel, self).__init__(selectedVariables, startValues, parent)
        self.modelDescription = None

    def setModelDescription(self, modelDescription):
        self.modelDescription = modelDescription

    def data(self, index, role):
        if not index.isValid():
            return None

        column = self.COLUMN_NAMES[index.column()]

        variable = index.internalPointer()

        if role == Qt.DisplayRole and column == 'Name':
            return variable.name

        return self.columnData(variable, column, role)

    def index(self, row, column, parent):
        variable = self.modelDescription.modelVariables[row]
        return self.createIndex(row, column, variable)

        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent):

        if self.modelDescription is None:
            return 0

        if parent.column() > 0:
            return 0

        if not parent.isValid():
            return len(self.modelDescription.modelVariables)

        return 0

    def variableForIndex(self, index):
        return self.modelDescription.modelVariables[index.row()]


class VariablesTreeModel(VariablesModel):

    def __init__(self, selectedVariables, startValues, parent=None):
        super(VariablesTreeModel, self).__init__(selectedVariables, startValues, parent)
        self.rootItem = TreeItem()

    def setModelDescription(self, md):

        self.rootItem.children[:] = []

        for variable in md.modelVariables:

            name = variable.name

            if name.startswith('der(') and name.endswith(')'):
                prefix, name, suffix = name[:4], name[4:-1], name[-1]
            else:
                prefix = suffix = ''

            segments = name.split('.')

            parentItem = self.rootItem

            for segment in segments[:-1]:
                p = parentItem.find(segment)
                if p is not None:
                    parentItem = p
                else:
                    p = TreeItem(name=segment)
                    parentItem.addChild(p)
                    parentItem = p

            parentItem.addChild(TreeItem(name=prefix + segments[-1] + suffix, variable=variable))

    def data(self, index, role):

        if not index.isValid():
            return None

        column = self.COLUMN_NAMES[index.column()]

        item = index.internalPointer()

        if role == Qt.DisplayRole and column == 'Name':
            return item.name

        if item.variable is None:
            if role == Qt.DecorationRole and column == 'Name':
                return QPixmap(":/icons/subsystem.png")
            else:
                return None

        return self.columnData(item.variable, column, role)

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.children[row]

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):

        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(index.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return len(parentItem.children)

    def variableForIndex(self, index):
        item = index.internalPointer()
        return item.variable


class VariablesFilterModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(VariablesFilterModel, self).__init__(parent)
        self.fixedFilterString = None
        self.filterByCausality = False
        self.filterParameters = True
        self.filterCalculatedParameters = False
        self.filterInputs = True
        self.filterOutputs = True
        self.filterIndependentVariables = True
        self.filterLocalVariables = False

    def setFilterFixedString(self, pattern):
        # print('pattern: "%s"' % pattern)
        self.fixedFilterString = pattern
        self.invalidateFilter()

    def setFilterByCausality(self, filter):
        self.filterByCausality = filter
        self.invalidateFilter()

    def setFilterParameters(self, filter):
        self.filterParameters = filter
        self.invalidateFilter()

    def setFilterCalculatedParameters(self, filter):
        self.filterCalculatedParameters = filter
        self.invalidateFilter()

    def setFilterInputs(self, filter):
        self.filterInputs = filter
        self.invalidateFilter()

    def setFilterOutputs(self, filter):
        self.filterOutputs = filter
        self.invalidateFilter()

    def setFilterIndependentVariables(self, filter):
        self.filterIndependentVariables = filter
        self.invalidateFilter()

    def setFilterLocalVariables(self, filter):
        self.filterLocalVariables = filter
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):

        index = self.sourceModel().index(source_row, 0, source_parent)
        item = index.internalPointer()

        if isinstance(item, TreeItem):
            if item.variable is None:
                return True
            else:
                variable = item.variable
        else:
            variable = item

        if self.filterByCausality:

            if variable.causality == 'parameter':
                if not self.filterParameters:
                    return False
            elif variable.causality == 'calculatedParameter':
                if not self.filterCalculatedParameters:
                    return False
            elif variable.causality == 'input':
                if not self.filterInputs:
                    return False
            elif variable.causality == 'output':
                if not self.filterOutputs:
                    return False
            elif variable.causality == 'independent':
                if not self.filterIndependentVariables:
                    return False
            else:
                if not self.filterLocalVariables:
                    return False

        if self.fixedFilterString:
            return self.fixedFilterString in variable.name
        else:
            return True
        # return super(VariablesFilterModel, self).filterAcceptsColumn(source_row, source_parent)
