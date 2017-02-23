from lxml import etree
import zipfile


class ModelDescription(object):

    def __init__(self):
        self.guid = None
        self.fmiVersion = None
        self.modelName = None
        self.description = None
        self.generationTool = None
        self.generationDateAndTime = None
        self.variableNamingConvention = None
        self.numberOfContinuousStates = None
        self.numberOfEventIndicators = None

        self.coSimulation = None
        self.modelExchange = None

        self.modelVariables = []


class CoSimulation(object):

    def __init__(self):
        self.modelIdentifier = None


class ModelExchange(object):

    def __init__(self):
        self.modelIdentifier = None


class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None
        self.type = None
        self.start = None
        self.causality = None
        self.variability = None

    def __repr__(self):
        return '%s "%s"' % (self.type, self.name)


def read_model_description(filename):

    with zipfile.ZipFile(filename, 'r') as zf:
        xml = zf.open('modelDescription.xml')
        tree = etree.parse(xml)

    root = tree.getroot()

    modelDescription = ModelDescription()

    modelDescription.guid = root.get('guid')
    modelDescription.fmiVersion = root.get('fmiVersion')
    modelDescription.modelName = root.get('modelName')
    modelDescription.description = root.get('description')
    modelDescription.generationTool = root.get('generationTool')
    modelDescription.generationDateAndTime = root.get('generationDateAndTime')
    modelDescription.variableNamingConvention = root.get('variableNamingConvention')
    modelDescription.numberOfContinuousStates = root.get('numberOfContinuousStates')
    modelDescription.numberOfEventIndicators = root.get('numberOfEventIndicators')

    if modelDescription.fmiVersion == "1.0":

        if root.find('Implementation') is not None:
            modelDescription.coSimulation = CoSimulation()
            modelDescription.coSimulation.modelIdentifier = root.get('modelIdentifier')
        else:
            modelDescription.modelExchange = ModelExchange()
            modelDescription.modelExchange.modelIdentifier = root.get('modelIdentifier')

        modelVariables = root.find('ModelVariables')

        for variable in modelVariables:

            if variable.get("name") is None:
                continue

            sv = ScalarVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')))
            sv.description = variable.get('description')
            sv.start = variable.get('start')
            sv.causality = variable.get('causality')

            value = next(variable.iterchildren())
            sv.type = value.tag
            start = value.get('start')

            if start is not None:
                if sv.type == 'Real':
                    sv.start = float(start)
                elif sv.type == 'Integer':
                    sv.start = int(start)
                elif sv.type == 'Boolean':
                    sv.start = start == 'true'
                else:
                    sv.start = start

            modelDescription.modelVariables.append(sv)


    return modelDescription
