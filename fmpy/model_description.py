from lxml import etree
import zipfile
import os

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


def read_model_description(filename, validate=True):

    with zipfile.ZipFile(filename, 'r') as zf:
        xml = zf.open('modelDescription.xml')
        tree = etree.parse(xml)

    root = tree.getroot()

    fmiVersion = root.get('fmiVersion')

    if not fmiVersion in ['1.0', '2.0']:
        raise Exception("Unsupported FMI version: %s" % fmiVersion)

    if validate:

        module_dir, _ = os.path.split(__file__)

        if fmiVersion == '1.0':
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi1', 'fmiModelDescription.xsd'))
        else:
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi2', 'fmi2ModelDescription.xsd'))

        if not schema.validate(root):
            message = "Failed to validate modelDescription.xml:"
            for entry in schema.error_log:
                message += "\n%s (line %d, column %d): %s" % (entry.level_name, entry.line, entry.column, entry.message)
            raise Exception(message)

    modelDescription = ModelDescription()
    modelDescription.fmiVersion = fmiVersion
    modelDescription.guid = root.get('guid')
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

        startTime = defaultExperiment.get('startTime')
        if startTime is not None:
            modelDescription.defaultExperiment.startTime = float(startTime)

        stopTime = defaultExperiment.get('stopTime')
        if stopTime is not None:
            modelDescription.defaultExperiment.stopTime = float(stopTime)

        tolerance = defaultExperiment.get('tolerance')
        if tolerance is not None:
            modelDescription.defaultExperiment.tolerance = float(tolerance)

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
