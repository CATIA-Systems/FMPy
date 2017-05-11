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

        self.defaultExperiment = None

        self.coSimulation = None
        self.modelExchange = None

        self.modelVariables = []


class DefaultExperiment(object):

    def __init__(self):
        self.startTime = None
        self.stopTime = None
        self.tolerance = None


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

    if root.get('numberOfEventIndicators') is not None:
        modelDescription.numberOfEventIndicators = int(root.get('numberOfEventIndicators'))

    if modelDescription.fmiVersion == '1.0':
        modelDescription.numberOfContinuousStates = int(root.get('numberOfContinuousStates'))
    else:
        modelDescription.numberOfContinuousStates = len(root.findall('ModelStructure/Derivatives/Unknown'))

    defaultExperiment = root.find('DefaultExperiment')

    if defaultExperiment is not None:
        modelDescription.defaultExperiment = DefaultExperiment()
        modelDescription.defaultExperiment.startTime = float(defaultExperiment.get('startTime'))
        modelDescription.defaultExperiment.stopTime = float(defaultExperiment.get('stopTime'))
        #modelDescription.defaultExperiment.tolerance = float(defaultExperiment.get('tolerance'))

    if modelDescription.fmiVersion == "1.0":

        modelIdentifier = root.get('modelIdentifier')

        if root.find('Implementation') is not None:
            modelDescription.coSimulation = CoSimulation()
            modelDescription.coSimulation.modelIdentifier = modelIdentifier
        else:
            modelDescription.modelExchange = ModelExchange()
            modelDescription.modelExchange.modelIdentifier = modelIdentifier

    else:

        me = root.find('ModelExchange')

        if me is not None:
            modelDescription.modelExchange = ModelExchange()
            modelDescription.modelExchange.modelIdentifier = me.get('modelIdentifier')

        cs = root.find('CoSimulation')

        if cs is not None:
            modelDescription.coSimulation = CoSimulation()
            modelDescription.coSimulation.modelIdentifier = cs.get('modelIdentifier')


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
