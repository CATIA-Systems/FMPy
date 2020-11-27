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
        self.numberOfContinuousStates = 0
        self.numberOfEventIndicators = 0

        self.defaultExperiment = None

        self.coSimulation = None
        self.modelExchange = None
        self.scheduledExecution = None

        self.buildConfigurations = []

        self.unitDefinitions = []
        self.typeDefinitions = []
        self.modelVariables = []

        # model structure
        self.outputs = []
        self.derivatives = []
        self.initialUnknowns = []
        self.eventIndicators = []


class DefaultExperiment(object):

    def __init__(self):
        self.startTime = None
        self.stopTime = None
        self.tolerance = None
        self.stepSize = None


class InterfaceType(object):

    def __init__(self):
        self.modelIdentifier = None
        self.needsExecutionTool = False
        self.canBeInstantiatedOnlyOncePerProcess = False
        self.canGetAndSetFMUstate = False
        self.canSerializeFMUstate = False
        self.providesDirectionalDerivative = False
        self.providesAdjointDerivatives = False
        self.providesPerElementDependencies = False

        # FMI 2.0
        self.canNotUseMemoryManagementFunctions = False
        self.providesDirectionalDerivative = False


class ModelExchange(InterfaceType):

    def __init__(self):
        super(ModelExchange, self).__init__()
        self.completedIntegratorStepNotNeeded = False


class CoSimulation(InterfaceType):

    def __init__(self):
        super(CoSimulation, self).__init__()
        self.canHandleVariableCommunicationStepSize = False
        self.canInterpolateInputs = False
        self.maxOutputDerivativeOrder = 0
        self.canRunAsynchronuously = False


class ScheduledExecution(CoSimulation):

    def __init__(self):
        super(ScheduledExecution, self).__init__()


class BuildConfiguration(object):

    def __init__(self):
        self.modelIdentifier = None
        self.sourceFileSets = []

    def __repr__(self):
        return 'BuildConfiguration %s' % self.sourceFileSets


class PreProcessorDefinition(object):

    def __init__(self):
        self.name = None
        self.value = None
        self.optional = False
        self.description = None

    def __repr__(self):
        return '%s=%s' % (self.name, self.value)


class SourceFileSet(object):

    def __init__(self):
        self.language = None
        self.preprocessorDefinitions = []
        self.sourceFiles = []
        self.includeDirectories = []

    def __repr__(self):
        return '%s %s' % (self.language, self.sourceFiles)


class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None

        self.type = None
        "One of 'Real', 'Integer', 'Enumeration', 'Boolean', 'String'"

        self.dimensions = []
        "List of fixed dimensions"

        self.dimensionValueReferences = []
        "List of value references to the variables that hold the dimensions"

        self.quantitiy = None
        "Physical quantity"

        self.unit = None
        "Unit"

        self.displayUnit = None
        "Default display unit"

        self.relativeQuantity = False
        "Relative quantity"

        self.min = None
        "Minimum value"

        self.max = None
        "Maximum value"

        self.nominal = None
        "Nominal value"

        self.unbounded = False
        "Value is unbounded"

        self.start = None
        "Initial or guess value"

        self.derivative = None
        "Derivative"

        self.causality = None
        "One of 'parameter', 'calculatedParameter', 'input', 'output', 'local', 'independent'"

        self.variability = None
        "One of 'constant', 'fixed', 'tunable', 'discrete' or 'continuous'"

        self.initial = None
        "One of 'exact', 'approx', 'calculated' or None"

        self.declaredType = None

        self.reinit = False
        "Can be reinitialized at an event by the FMU"

        self.sourceline = None
        "Line number in the modelDescription.xml or None if unknown"

    def __repr__(self):
        return '%s "%s"' % (self.type, self.name)


class Dimension(object):

    def __init__(self, **kwargs):
        self.start = kwargs.get('start')
        self.valueReference = kwargs.get('valueReference')


class SimpleType(object):
    """ Type Definition """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        self.quantity = kwargs.get('quantity')
        self.unit = kwargs.get('unit')
        self.displayUnit = kwargs.get('displayUnit')
        self.relativeQuantity = kwargs.get('relativeQuantity')
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self.nominal = kwargs.get('nominal')
        self.unbounded = kwargs.get('unbounded')
        self.items = kwargs.get('items', [])

    def __repr__(self):
        return '%s "%s" [%s]' % (self.type, self.name, self.unit)


class Item(object):
    """ Enumeration Item """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.value = kwargs.get('value')
        self.description = kwargs.get('description')

    def __repr__(self):
        return '%s (%s) %s' % (self.name, self.value, self.description)


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
        self.sourceline = None
        "Line number in the modelDescription.xml"

    def __repr__(self):
        return '%s' % self.variable


def _copy_attributes(element, object, attributes=None):
    """ Copy attributes from an XML element to a Python object """

    if attributes is None:
        attributes = object.__dict__.keys()

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


def read_build_description(filename, validate=True):

    import zipfile
    from lxml import etree
    import os
    from .util import _is_string

    if _is_string(filename) and os.path.isdir(filename):  # extracted FMU
        filename = os.path.join(filename, 'sources/buildDescription.xml')
        if not os.path.isfile(filename):
            return []
        tree = etree.parse(filename)
    elif _is_string(filename) and os.path.isfile(filename) and filename.lower().endswith('.xml'):  # XML file
        if not os.path.isfile(filename):
            return []
        tree = etree.parse(filename)
    else:  # FMU as path or file like object
        with zipfile.ZipFile(filename, 'r') as zf:
            if 'sources/buildDescription.xml' not in zf.namelist():
                return []
            xml = zf.open('sources/buildDescription.xml')
            tree = etree.parse(xml)

    root = tree.getroot()

    fmi_version = root.get('fmiVersion')

    if fmi_version is None or not fmi_version.startswith('3.0'):
        raise Exception("Unsupported fmiBuildDescription version: %s" % fmi_version)

    if validate:

        module_dir, _ = os.path.split(__file__)
        schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi3', 'fmi3BuildDescription.xsd'))

        if not schema.validate(root):
            message = "Failed to validate buildDescription.xml:"
            for entry in schema.error_log:
                message += "\n%s (line %d, column %d): %s" % (entry.level_name, entry.line, entry.column, entry.message)
            raise Exception(message)

    build_configurations = []

    for bc in root.findall('BuildConfiguration'):

        buildConfiguration = BuildConfiguration()
        buildConfiguration.modelIdentifier = bc.get('modelIdentifier')

        build_configurations.append(buildConfiguration)

        for sf in bc.findall('SourceFileSet'):

            sourceFileSet = SourceFileSet()
            sourceFileSet.language = sf.get('language')

            for pd in sf.findall('PreprocessorDefinition'):
                definition = PreProcessorDefinition()
                definition.name = pd.get('name')
                definition.value = pd.get('value')
                definition.optional = pd.get('optional') == 'true'
                definition.description = pd.get('description')
                sourceFileSet.preprocessorDefinitions.append(definition)

            for f in sf.findall('SourceFile'):
                sourceFileSet.sourceFiles.append(f.get('name'))

            for d in sf.findall('IncludeDirectory'):
                sourceFileSet.includeDirectories.append(d.get('name'))

            buildConfiguration.sourceFileSets.append(sourceFileSet)

    return build_configurations


def read_model_description(filename, validate=True, validate_variable_names=False, validate_model_structure=False):
    """ Read the model description from an FMU without extracting it

    Parameters:
        filename                  filename of the FMU or XML file, directory with extracted FMU or file like object
        validate                  whether the model description should be validated
        validate_variable_names   validate the variable names against the EBNF
        validate_model_structure  validate the model structure

    returns:
        model_description   a ModelDescription object
    """

    import zipfile
    from lxml import etree
    import os
    from .util import _is_string
    from . import validation

    # remember the original filename
    _filename = filename

    if _is_string(filename) and os.path.isdir(filename):  # extracted FMU
        filename = os.path.join(filename, 'modelDescription.xml')
        tree = etree.parse(filename)
    elif _is_string(filename) and os.path.isfile(filename) and filename.lower().endswith('.xml'):  # XML file
        tree = etree.parse(filename)
    else:  # FMU as path or file like object
        with zipfile.ZipFile(filename, 'r') as zf:
            xml = zf.open('modelDescription.xml')
            tree = etree.parse(xml)

    root = tree.getroot()

    fmiVersion = root.get('fmiVersion')

    is_fmi1 = fmiVersion == '1.0'
    is_fmi2 = fmiVersion == '2.0'
    is_fmi3 = fmiVersion.startswith('3.0')

    if not is_fmi1 and not is_fmi2 and not is_fmi3:
        raise Exception("Unsupported FMI version: %s" % fmiVersion)

    if validate:

        module_dir, _ = os.path.split(__file__)

        if is_fmi1:
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi1', 'fmiModelDescription.xsd'))
        elif is_fmi2:
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi2', 'fmi2ModelDescription.xsd'))
        else:
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi3', 'fmi3ModelDescription.xsd'))

        if not schema.validate(root):
            message = "Failed to validate modelDescription.xml:"
            for entry in schema.error_log:
                message += "\n%s (line %d, column %d): %s" % (entry.level_name, entry.line, entry.column, entry.message)
            raise Exception(message)

    modelDescription = ModelDescription()
    _copy_attributes(root, modelDescription, ['fmiVersion', 'guid', 'modelName', 'description', 'generationTool',
                                              'generationDateAndTime', 'variableNamingConvention'])

    if is_fmi3:
        modelDescription.guid = root.get('instantiationToken')

    if root.get('numberOfEventIndicators') is not None:
        modelDescription.numberOfEventIndicators = int(root.get('numberOfEventIndicators'))

    if is_fmi1:
        modelDescription.numberOfContinuousStates = int(root.get('numberOfContinuousStates'))
    elif is_fmi2:
        modelDescription.numberOfContinuousStates = len(root.findall('ModelStructure/Derivatives/Unknown'))
    else:
        modelDescription.numberOfContinuousStates = len(root.findall('ModelStructure/Derivative'))

    # default experiment
    for d in root.findall('DefaultExperiment'):

        modelDescription.defaultExperiment = DefaultExperiment()

        for attribute in ['startTime', 'stopTime', 'tolerance', 'stepSize']:
            if attribute in d.attrib:
                setattr(modelDescription.defaultExperiment, attribute, float(d.get(attribute)))

    # model description
    if is_fmi1:

        modelIdentifier = root.get('modelIdentifier')

        if root.find('Implementation') is not None:
            modelDescription.coSimulation = CoSimulation()
            modelDescription.coSimulation.modelIdentifier = modelIdentifier
        else:
            modelDescription.modelExchange = ModelExchange()
            modelDescription.modelExchange.modelIdentifier = modelIdentifier

    elif is_fmi2:

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

    else:

        for me in root.findall('ModelExchange'):
            modelDescription.modelExchange = ModelExchange()
            _copy_attributes(me, modelDescription.modelExchange)

        for cs in root.findall('CoSimulation'):
            modelDescription.coSimulation = CoSimulation()
            _copy_attributes(cs, modelDescription.coSimulation)

        for se in root.findall('ScheduledExecution'):
            modelDescription.scheduledExecution = ScheduledExecution()
            _copy_attributes(se, modelDescription.scheduledExecution)

    # build configurations
    if is_fmi2:

        for interface_type in root.findall('ModelExchange') + root.findall('CoSimulation'):

            modelIdentifier = interface_type.get('modelIdentifier')

            if len(modelDescription.buildConfigurations) > 0 and modelDescription.buildConfigurations[0].modelIdentifier == modelIdentifier:
                continue  # use existing build configuration for both FMI types

            source_files = [file.get('name') for file in interface_type.findall('SourceFiles/File')]

            if len(source_files) > 0:
                buildConfiguration = BuildConfiguration()
                modelDescription.buildConfigurations.append(buildConfiguration)
                buildConfiguration.modelIdentifier = modelIdentifier
                source_file_set = SourceFileSet()
                buildConfiguration.sourceFileSets.append(source_file_set)
                source_file_set.sourceFiles = source_files

    elif is_fmi3 and not (_is_string(_filename) and _filename.endswith('.xml')):
        # read buildDescription.xml if _filename is a folder or ZIP file
        modelDescription.buildConfigurations = read_build_description(_filename, validate=validate)

    # unit definitions
    if is_fmi1:

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
    type_definitions = {None: None}

    if is_fmi1 or is_fmi2:
        # FMI 1 and 2
        for t in root.findall('TypeDefinitions/' + ('Type' if is_fmi1 else 'SimpleType')):

            first = t[0]  # first element

            simple_type = SimpleType(
                name=t.get('name'),
                type=first.tag[:-len('Type')] if is_fmi1 else first.tag,
                **first.attrib
            )

            # add enumeration items
            for i, item in enumerate(first.findall('Item')):
                it = Item(**item.attrib)
                if is_fmi1:
                    it.value = i + 1
                simple_type.items.append(it)

            modelDescription.typeDefinitions.append(simple_type)
            type_definitions[simple_type.name] = simple_type
    else:
        # FMI 3
        for t in root.findall('TypeDefinitions/*'):

            if t.tag not in {'Float32Type', 'Float64Type', 'Int8Type', 'UInt8Type', 'Int16Type', 'UInt16Type', 'Int32Type',
                             'UInt32Type', 'Int64Type', 'UInt64Type', 'BooleanType', 'StringType', 'BinaryType',
                             'EnumerationType'}:
                continue

            simple_type = SimpleType(type=t.tag[:-4], **t.attrib)

            # add enumeration items
            for item in t.findall('Item'):
                it = Item(**item.attrib)
                simple_type.items.append(it)

            modelDescription.typeDefinitions.append(simple_type)
            type_definitions[simple_type.name] = simple_type

    # default values for 'initial' derived from variability and causality
    initial_defaults = {
        'constant':   {'output': 'exact', 'local': 'exact', 'parameter': 'exact'},
        'fixed':      {'parameter': 'exact', 'calculatedParameter': 'calculated', 'local': 'calculated'},
        'tunable':    {'parameter': 'exact', 'calculatedParameter': 'calculated', 'structuralParameter': 'exact', 'local': 'calculated'},
        'discrete':   {'input': None, 'output': 'calculated', 'local': 'calculated'},
        'continuous': {'input': None, 'output': 'calculated', 'local': 'calculated', 'independent': None},
        'clock':      {'input': None, 'output': None},
    }

    # model variables
    for variable in root.find('ModelVariables'):

        if variable.get("name") is None:
            continue

        sv = ScalarVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')))
        sv.description = variable.get('description')
        sv.causality = variable.get('causality', default='local')
        sv.variability = variable.get('variability')
        sv.initial = variable.get('initial')
        sv.sourceline = variable.sourceline

        if fmiVersion in ['1.0', '2.0']:
            # get the nested "value" element
            for child in variable.iterchildren():
                if child.tag in {'Real', 'Integer', 'Boolean', 'String', 'Enumeration'}:
                    value = child
                    break
        else:
            value = variable

        sv.type = value.tag

        if variable.tag == 'String':
            # handle <Start> element of String variables in FMI 3
            sv.start = variable.find('Start').get('value')
        else:
            sv.start = value.get('start')

        type_map = {
            'Real':        float,
            'Integer':     int,
            'Enumeration': int,
            'Boolean':     bool,
            'String':      str,

            'Float32':     float,
            'Float64':     float,
            'Int8':        int,
            'UInt8':       int,
            'Int16':       int,
            'UInt16':      int,
            'Int32':       int,
            'UInt32':      int,
            'Int64':       int,
            'UInt64':      int,
            'Binary':      bytes,
            'Clock':       float,
        }

        sv._python_type = type_map[sv.type]

        if sv.type in ['Real', 'Float32', 'Float64']:
            sv.unit = value.get('unit')
            sv.displayUnit = value.get('displayUnit')
            sv.relativeQuantity = value.get('relativeQuantity') == 'true'
            sv.derivative = value.get('derivative')
            sv.nominal = value.get('nominal')
            sv.unbounded = value.get('unbounded') == 'true'

        if sv.type in ['Real', 'Enumeration'] or sv.type.startswith(('Float', 'Int')):
            sv.quantity = value.get('quantity')
            sv.min = value.get('min')
            sv.max = value.get('max')

        # resolve the declared type
        declared_type = value.get('declaredType')
        if declared_type in type_definitions:
            sv.declaredType = type_definitions[value.get('declaredType')]
        else:
            raise Exception('Variable "%s" (line %s) has declaredType="%s" which has not been defined.'
                            % (sv.name, sv.sourceline, declared_type))

        if is_fmi1:
            if sv.causality == 'internal':
                sv.causality = 'local'

            if sv.variability == 'parameter':
                sv.causality = 'parameter'
                sv.variability = None
        else:
            if sv.variability is None:
                sv.variability = 'continuous' if sv.type in {'Float32', 'Float64', 'Real'} else 'discrete'

            if sv.initial is None:
                try:
                    sv.initial = initial_defaults[sv.variability][sv.causality]
                except KeyError:
                    raise Exception('Variable "%s" (line %s) has an illegal combination of causality="%s"'
                                    ' and variability="%s".' % (sv.name, sv.sourceline, sv.causality, sv.variability))

        dimensions = variable.findall('Dimension')

        if dimensions:
            for dimension in dimensions:
                start = dimension.get('start')
                vr = dimension.get('valueReference')
                d = Dimension(
                    start=int(start) if start is not None else None,
                    valueReference=int(vr) if vr is not None else None
                )
                sv.dimensions.append(d)

        modelDescription.modelVariables.append(sv)

    variables = dict((v.valueReference, v) for v in modelDescription.modelVariables)

    # calculate initial shape
    for variable in modelDescription.modelVariables:

        shape = []

        for d in variable.dimensions:

            if d.start is not None:
                shape.append(int(d.start))
            else:
                v = variables[d.valueReference]
                shape.append(int(v.start))

        variable.shape = tuple(shape)

    if is_fmi2:

        # model structure
        for attr, element in [(modelDescription.outputs, 'Outputs'),
                              (modelDescription.derivatives, 'Derivatives'),
                              (modelDescription.initialUnknowns, 'InitialUnknowns')]:

            for u in root.findall('ModelStructure/' + element + '/Unknown'):
                unknown = Unknown()
                unknown.sourceline = u.sourceline
                unknown.variable = modelDescription.modelVariables[int(u.get('index')) - 1]

                dependencies = u.get('dependencies')

                if dependencies:
                    for vr in dependencies.strip().split(' '):
                        unknown.dependencies.append(modelDescription.modelVariables[int(vr) - 1])

                dependenciesKind = u.get('dependenciesKind')

                if dependenciesKind:
                    unknown.dependenciesKind = dependenciesKind.strip().split(' ')

                attr.append(unknown)

        # resolve derivatives
        for variable in modelDescription.modelVariables:
            if variable.derivative is not None:
                index = int(variable.derivative) - 1
                variable.derivative = modelDescription.modelVariables[index]

    if is_fmi3:

        for attr, element in [(modelDescription.outputs, 'Output'),
                              (modelDescription.derivatives, 'Derivative'),
                              (modelDescription.initialUnknowns, 'InitialUnknown'),
                              (modelDescription.eventIndicators, 'EventIndicator')]:

            for u in root.findall('ModelStructure/' + element):
                unknown = Unknown()
                unknown.sourceline = u.sourceline
                unknown.variable = variables[int(u.get('valueReference'))]

                dependencies = u.get('dependencies')

                if dependencies:
                    for vr in dependencies.strip().split(' '):
                        unknown.dependencies.append(variables[int(vr)])

                dependenciesKind = u.get('dependenciesKind')

                if dependenciesKind:
                    unknown.dependenciesKind = dependenciesKind.strip().split(' ')

                attr.append(unknown)

        modelDescription.numberOfEventIndicators = len(modelDescription.eventIndicators)

        # resolve derivatives
        for variable in modelDescription.modelVariables:
            if variable.derivative is not None:
                variable.derivative = modelDescription.modelVariables[int(variable.derivative)]

    problems = []

    if validate:
        problems += validation.validate_model_description(modelDescription,
                                                          validate_variable_names=validate_variable_names,
                                                          validate_model_structure=validate_model_structure)

    if problems:
        message = ("Failed to validate model description. %d problems were found:\n\n- " % len(problems)) + '\n- '.join(problems)
        raise Exception(message)

    return modelDescription
