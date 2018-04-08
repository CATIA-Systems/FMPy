""" Object model and loader for the modelDescription.xml """


class ModelDescription(object):

    def __init__(self):
        self.guid = None
        self.fmiVersion = None
        self.modelName = None
        self.description = None
        self.generationTool = None
        self.generationDateAndTime = None
        self.variableNamingConvention = 'flat'
        self.numberOfContinuousStates = None
        self.numberOfEventIndicators = None

        self.defaultExperiment = None

        self.coSimulation = None
        self.modelExchange = None

        self.unitDefinitions = []
        self.typeDefinitions = []
        self.modelVariables = []

        self.outputs = []
        self.derivatives = []
        self.initialUnknowns = []


class DefaultExperiment(object):

    def __init__(self):
        self.startTime = None
        self.stopTime = None
        self.tolerance = None
        self.stepSize = None


class CoSimulation(object):

    def __init__(self):
        self.modelIdentifier = None
        self.needsExecutionTool = False
        self.canHandleVariableCommunicationStepSize = False
        self.canInterpolateInputs = False
        self.maxOutputDerivativeOrder = 0
        self.canRunAsynchronuously = False
        self.canBeInstantiatedOnlyOncePerProcess = False
        self.canNotUseMemoryManagementFunctions = False
        self.canGetAndSetFMUstate = False
        self.canSerializeFMUstate = False
        self.providesDirectionalDerivative = False
        self.sourceFiles = []


class ModelExchange(object):

    def __init__(self):
        self.modelIdentifier = None
        self.needsExecutionTool = False
        self.completedIntegratorStepNotNeeded = False
        self.canBeInstantiatedOnlyOncePerProcess = False
        self.canNotUseMemoryManagementFunctions = False
        self.canGetAndSetFMUstate = False
        self.canSerializeFMUstate = False
        self.providesDirectionalDerivative = False
        self.sourceFiles = []


class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None

        self.type = None
        "One of 'Real', 'Integer', 'Enumeration', 'Boolean', 'String'"

        self.unit = None

        self.start = None

        self.causality = None
        "One of 'parameter', 'calculatedParameter', 'input', 'output', 'local', 'independent'"

        self.variability = None
        "One of 'constant', 'fixed', 'tunable', 'discrete' or 'continuous'"

        self.initial = None
        "One of 'exact', 'approx', 'calculated' or None"

        self.declaredType = None

    def __repr__(self):
        return '%s "%s"' % (self.type, self.name)


class SimpleType(object):

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.quantity = None
        self.unit = None
        self.displayUnit = None
        self.relativeQuantity = None
        self.min = None
        self.max = None
        self.nominal = None
        self.unbounded = None

    def __repr__(self):
        return '%s "%s" [%s]' % (self.type, self.name, self.unit)


class Unit(object):

    def __init__(self, name):
        self.name = name
        self.baseUnit = None
        self.displayUnits = []

    def __repr__(self):
        return '%s' % self.name


class BaseUnit(object):

    def __init__(self):
        self.kg = 0
        self.m = 0
        self.s = 0
        self.A = 0
        self.K = 0
        self.mol = 0
        self.cd = 0
        self.rad = 0
        self.factor = 1.0
        self.offset = 0.0

    def __repr__(self):
        return "kg=%d, m=%d, s=%d, A=%d, K=%d, mol=%d, cd=%d, rad=%d, factor=%g, offset=%g" % (
            self.kg, self.m, self.s, self.A, self.K, self.mol, self.cd, self.rad, self.factor, self.offset)


class DisplayUnit(object):

    def __init__(self, name):
        self.name = name
        self.factor = 1.0
        self.offset = 0.0

    def __repr__(self):
        return '%s' % self.name


class Unknown(object):

    def __init__(self):

        self.index = 0
        self.variable = None
        self.dependencies = []
        self.dependenciesKind = []

    def __repr__(self):
        return '%s' % self.variable


def _copy_attributes(element, object, attributes):
    """ Copy attributes from an XML element to a Python object """

    for attribute in attributes:

        if attribute not in element.attrib:
            continue  # skip

        value = element.get(attribute)

        t = type(getattr(object, attribute))

        # convert the value to the correct type
        if t is bool:
            value = value == 'true'
        elif t is int:
            value = int(value)
        elif t is float:
            value = float(value)

        setattr(object, attribute, value)


def read_model_description(filename, validate=True):
    """ Read the model description from an FMU without extracting it

    Parameters:
        filename   filename of the FMU or directory with extracted FMU
        validate   whether the model description should be validated

    returns:
        model_description   a ModelDescription object
    """

    import zipfile
    from lxml import etree
    import os

    xml_file = os.path.join(filename, 'modelDescription.xml')

    if os.path.isfile(xml_file):
        tree = etree.parse(xml_file)
    else:
        with zipfile.ZipFile(filename, 'r') as zf:
            xml = zf.open('modelDescription.xml')
            tree = etree.parse(xml)

    root = tree.getroot()

    fmiVersion = root.get('fmiVersion')

    if fmiVersion not in ['1.0', '2.0']:
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
    _copy_attributes(root, modelDescription, ['fmiVersion', 'guid', 'modelName', 'description', 'generationTool',
                                              'generationDateAndTime', 'variableNamingConvention'])

    if root.get('numberOfEventIndicators') is not None:
        modelDescription.numberOfEventIndicators = int(root.get('numberOfEventIndicators'))

    if fmiVersion == '1.0':
        modelDescription.numberOfContinuousStates = int(root.get('numberOfContinuousStates'))
    else:
        modelDescription.numberOfContinuousStates = len(root.findall('ModelStructure/Derivatives/Unknown'))

    # default experiment
    for d in root.findall('DefaultExperiment'):

        modelDescription.defaultExperiment = DefaultExperiment()

        for attribute in ['startTime', 'stopTime', 'tolerance', 'stepSize']:
            if attribute in d.attrib:
                setattr(modelDescription.defaultExperiment, attribute, float(d.get(attribute)))

    # model description
    if fmiVersion == "1.0":

        modelIdentifier = root.get('modelIdentifier')

        if root.find('Implementation') is not None:
            modelDescription.coSimulation = CoSimulation()
            modelDescription.coSimulation.modelIdentifier = modelIdentifier
        else:
            modelDescription.modelExchange = ModelExchange()
            modelDescription.modelExchange.modelIdentifier = modelIdentifier

    else:

        for me in root.findall('ModelExchange'):
            modelDescription.modelExchange = ModelExchange()
            _copy_attributes(me, modelDescription.modelExchange,
                             ['modelIdentifier',
                              'needsExecutionTool',
                              'completedIntegratorStepNotNeeded',
                              'canBeInstantiatedOnlyOncePerProcess',
                              'canNotUseMemoryManagementFunctions',
                              'canGetAndSetFMUstate',
                              'canSerializeFMUstate',
                              'providesDirectionalDerivative'])
            for file in me.findall('SourceFiles/File'):
                modelDescription.modelExchange.sourceFiles.append(file.get('name'))

        for cs in root.findall('CoSimulation'):
            modelDescription.coSimulation = CoSimulation()
            _copy_attributes(cs, modelDescription.coSimulation,
                             ['modelIdentifier',
                              'needsExecutionTool',
                              'canHandleVariableCommunicationStepSize',
                              'canInterpolateInputs',
                              'maxOutputDerivativeOrder',
                              'canRunAsynchronuously',
                              'canBeInstantiatedOnlyOncePerProcess',
                              'canNotUseMemoryManagementFunctions',
                              'canGetAndSetFMUstate',
                              'canSerializeFMUstate',
                              'providesDirectionalDerivative'])
            for file in cs.findall('SourceFiles/File'):
                modelDescription.coSimulation.sourceFiles.append(file.get('name'))

    # unit definitions
    if fmiVersion == "1.0":

        for u in root.findall('UnitDefinitions/BaseUnit'):
            unit = Unit(name=u.get('unit'))

            for d in u.findall('DisplayUnitDefinition'):
                displayUnit = DisplayUnit(name=d.get('displayUnit'))
                displayUnit.factor = float(d.get('gain', '1'))
                displayUnit.offset = float(d.get('offset', '0'))
                unit.displayUnits.append(displayUnit)

            modelDescription.unitDefinitions.append(unit)

    else:

        for u in root.findall('UnitDefinitions/Unit'):
            unit = Unit(name=u.get('name'))

            # base unit
            for b in u.findall('BaseUnit'):
                unit.baseUnit = BaseUnit()
                _copy_attributes(b, unit.baseUnit, ['kg', 'm', 's', 'A', 'K', 'mol', 'cd', 'rad', 'factor', 'offset'])

            # display units
            for d in u.findall('DisplayUnit'):
                displayUnit = DisplayUnit(name=d.get('name'))
                _copy_attributes(d, displayUnit, ['factor', 'offset'])
                unit.displayUnits.append(displayUnit)

            modelDescription.unitDefinitions.append(unit)

    # type definitions
    typeDefinitions = {None: None}

    for t in root.findall('TypeDefinitions/' + ('Type' if fmiVersion == "1.0" else 'SimpleType')):
        simpleType = SimpleType(name=t.get('name'), type=t[0].tag[:-len('Type')])

        for attribute in ['quantity', 'unit', 'displayUnit', 'relativeQuantity', 'min', 'max', 'nominal', 'unbounded']:
            setattr(simpleType, attribute, t[0].get(attribute))

        # TODO: add enumeration items

        modelDescription.typeDefinitions.append(simpleType)
        typeDefinitions[simpleType.name] = simpleType

    # default values for 'initial' derived from variability and causality
    initial_defaults = {
        'constant':   {'output': 'exact', 'local': 'exact'},
        'fixed':      {'parameter': 'exact', 'calculatedParameter': 'calculated', 'local': 'calculated'},
        'tunable':    {'parameter': 'exact', 'calculatedParameter': 'calculated', 'local': 'calculated'},
        'discrete':   {'input': None, 'output': 'calculated', 'local': 'calculated'},
        'continuous': {'input': None, 'output': 'calculated', 'local': 'calculated', 'independent': None},
    }

    # model variables
    for variable in root.find('ModelVariables'):

        if variable.get("name") is None:
            continue

        sv = ScalarVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')))
        sv.description = variable.get('description')
        sv.start = variable.get('start')
        sv.causality = variable.get('causality', default='local')
        sv.variability = variable.get('variability')
        sv.initial = variable.get('initial')

        value = next(variable.iterchildren())
        sv.type = value.tag
        sv.start = value.get('start')

        if sv.type == 'Real':
            sv.unit = value.get('unit')

        # resolve the declared type
        sv.declaredType = typeDefinitions[value.get('declaredType')]

        if fmiVersion == '1.0':
            if sv.causality == 'internal':
                sv.causality = 'local'

            if sv.variability == 'parameter':
                sv.causality = 'parameter'
                sv.variability = None
        else:
            if sv.variability is None:
                if sv.type == 'Real':
                    sv.variability = 'continuous'
                else:
                    sv.variability = 'discrete'

            if sv.initial is None:
                sv.initial = initial_defaults[sv.variability][sv.causality]

        modelDescription.modelVariables.append(sv)

    # model structure
    for attr, element in [(modelDescription.outputs, 'Outputs'),
                          (modelDescription.derivatives, 'Derivatives'),
                          (modelDescription.initialUnknowns, 'InitialUnknowns')]:

        for u in root.findall('ModelStructure/' + element + '/Unknown'):
            unknown = Unknown()

            unknown.variable = modelDescription.modelVariables[int(u.get('index')) - 1]

            dependencies = u.get('dependencies')

            if dependencies:
                for i in dependencies.split(' '):
                    unknown.dependencies.append(modelDescription.modelVariables[int(i) - 1])

            dependenciesKind = u.get('dependenciesKind')

            if dependenciesKind:
                unknown.dependenciesKind = u.get('dependenciesKind').split(' ')

            attr.append(unknown)

    return modelDescription
