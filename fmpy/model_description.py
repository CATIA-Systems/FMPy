""" Object model and loader for the modelDescription.xml """

from typing import List, Union, IO
from attr import attrs, attrib, Factory


@attrs(auto_attribs=True)
class DefaultExperiment(object):

    startTime: str = None
    stopTime: str = None
    tolerance: str = None
    stepSize: str = None


@attrs(eq=False)
class InterfaceType(object):

    modelIdentifier = attrib(type=str, default=None)
    needsExecutionTool = attrib(type=bool, default=False, repr=False)
    canBeInstantiatedOnlyOncePerProcess = attrib(type=bool, default=False, repr=False)
    canGetAndSetFMUstate = attrib(type=bool, default=False, repr=False)
    canSerializeFMUstate = attrib(type=bool, default=False, repr=False)
    providesDirectionalDerivative = attrib(type=bool, default=False, repr=False)
    providesAdjointDerivatives = attrib(type=bool, default=False, repr=False)
    providesPerElementDependencies = attrib(type=bool, default=False, repr=False)

    # FMI 2.0
    canNotUseMemoryManagementFunctions = attrib(type=bool, default=False, repr=False)
    providesDirectionalDerivative = attrib(type=bool, default=False, repr=False)


@attrs(eq=False)
class ModelExchange(InterfaceType):

    needsCompletedIntegratorStep = attrib(type=bool, default=False, repr=False)
    providesEvaluateDiscreteStates = attrib(type=bool, default=False, repr=False)


@attrs(eq=False)
class CoSimulation(InterfaceType):

    canHandleVariableCommunicationStepSize = attrib(type=bool, default=False, repr=False)
    fixedInternalStepSize = attrib(type=float, default=None, repr=False)
    maxOutputDerivativeOrder = attrib(type=int, default=0, repr=False)
    recommendedIntermediateInputSmoothness = attrib(type=int, default=0, repr=False)
    canInterpolateInputs = attrib(type=bool, default=False, repr=False)
    providesIntermediateUpdate = attrib(type=bool, default=False, repr=False)
    canReturnEarlyAfterIntermediateUpdate = attrib(type=bool, default=False, repr=False)
    hasEventMode = attrib(type=bool, default=False, repr=False)
    providesEvaluateDiscreteStates = attrib(type=bool, default=False, repr=False)
    canRunAsynchronuously = attrib(type=bool, default=False, repr=False)


@attrs(eq=False)
class ScheduledExecution(InterfaceType):

    pass


@attrs(auto_attribs=True, eq=False)
class PreProcessorDefinition(object):

    name: str = None
    value: str = None
    optional: bool = False
    description: str = None


@attrs(auto_attribs=True, eq=False)
class SourceFileSet(object):

    name: str = None
    language: str = None
    compiler: str = None
    compilerOptions: str = None
    preprocessorDefinitions: List[str] = Factory(list)
    sourceFiles: List[str] = Factory(list)
    includeDirectories: List[str] = Factory(list)


@attrs(auto_attribs=True, eq=False)
class BuildConfiguration(object):

    modelIdentifier: str = None
    sourceFileSets: List[SourceFileSet] = Factory(list)


@attrs(eq=False)
class Dimension(object):

    start = attrib(type=str)
    valueReference = attrib(type=int)


@attrs(eq=False)
class Item(object):
    """ Enumeration Item """

    name = attrib(type=str, default=None)
    value = attrib(type=str, default=None)
    description = attrib(type=str, default=None, repr=False)


@attrs(eq=False)
class SimpleType(object):
    """ Type Definition """

    name = attrib(type=str, default=None)
    type = attrib(type=str, default=None)
    quantity = attrib(type=str, default=None, repr=False)
    unit = attrib(type=str, default=None)
    displayUnit = attrib(type=str, default=None, repr=False)
    relativeQuantity = attrib(type=str, default=None, repr=False)
    min = attrib(type=str, default=None, repr=False)
    max = attrib(type=str, default=None, repr=False)
    nominal = attrib(type=str, default=None, repr=False)
    unbounded = attrib(type=str, default=None, repr=False)
    items = attrib(type=List[Item], default=Factory(list), repr=False)


@attrs(eq=False)
class DisplayUnit(object):

    name = attrib(type=str, default=None)
    factor = attrib(type=float, default=1.0, repr=False)
    offset = attrib(type=float, default=0.0, repr=False)


@attrs(eq=False)
class Unit(object):

    name = attrib(type=str, default=None)
    baseUnit = attrib(type=str, default=None, repr=False)
    displayUnits = attrib(type=List[DisplayUnit], default=Factory(list), repr=False)


@attrs(eq=False)
class BaseUnit(object):

    kg = attrib(type=int, default=0)
    m = attrib(type=int, default=0)
    s = attrib(type=int, default=0)
    A = attrib(type=int, default=0)
    K = attrib(type=int, default=0)
    mol = attrib(type=int, default=0)
    cd = attrib(type=int, default=0)
    rad = attrib(type=int, default=0)
    factor = attrib(type=float, default=1.0)
    offset = attrib(type=float, default=0.0)


@attrs(eq=False)
class ScalarVariable(object):

    name = attrib(type=str)

    valueReference = attrib(type=int, repr=False)

    type = attrib(type=str, default=None)
    "One of 'Real', 'Integer', 'Enumeration', 'Boolean', 'String'"

    description = attrib(type=str, default=None, repr=False)

    causality = attrib(type=str, default=None, repr=False)
    "One of 'parameter', 'calculatedParameter', 'input', 'output', 'local', 'independent'"

    variability = attrib(type=str, default=None, repr=False)
    "One of 'constant', 'fixed', 'tunable', 'discrete' or 'continuous'"

    initial = attrib(type=str, default=None, repr=False)
    "One of 'exact', 'approx', 'calculated' or None"

    canHandleMultipleSetPerTimeInstant = attrib(type=bool, default=True, repr=False)

    intermediateUpdate = attrib(type=bool, default=False, repr=False)

    previous = attrib(type=int, default=None, repr=False)

    # TODO: resolve variables
    clocks = attrib(type=List[int], default=Factory(list))

    declaredType = attrib(type=SimpleType, default=None, repr=False)

    dimensions = attrib(type=List[Dimension], default=Factory(list))
    "List of fixed dimensions"

    dimensionValueReferences = attrib(type=List[int], default=Factory(list))
    "List of value references to the variables that hold the dimensions"

    quantity = attrib(type=str, default=None, repr=False)
    "Physical quantity"

    unit = attrib(type=str, default=None, repr=False)
    "Unit"

    displayUnit = attrib(type=str, default=None, repr=False)
    "Default display unit"

    relativeQuantity = attrib(type=bool, default=False, repr=False)
    "Relative quantity"

    min = attrib(type=str, default=None, repr=False)
    "Minimum value"

    max = attrib(type=str, default=None, repr=False)
    "Maximum value"

    nominal = attrib(type=str, default=None, repr=False)
    "Nominal value"

    unbounded = attrib(type=bool, default=False, repr=False)
    "Value is unbounded"

    start = attrib(type=str, default=None, repr=False)
    "Initial or guess value"

    derivative = attrib(type='ScalarVariable', default=None, repr=False)
    "The derivative of this variable"

    reinit = attrib(type=bool, default=False, repr=False)
    "Can be reinitialized at an event by the FMU"

    sourceline = attrib(type=int, default=None, repr=False)
    "Line number in the modelDescription.xml or None if unknown"

    # Clock attributes
    canBeDeactivated = attrib(type=bool, default=False, repr=False)

    priority = attrib(type=int, default=None, repr=False)

    intervalVariability = attrib(type=str, default=None, repr=False)
    "One of 'constant', 'fixed', 'tunable', 'changing', 'countdown', 'triggered' or None"

    computed = attrib(type=bool, default=False, repr=False)

    intervalDecimal = attrib(type=float, default=None, repr=False)

    shiftDecimal = attrib(type=float, default=None, repr=False)

    supportsFraction = attrib(type=bool, default=False, repr=False)

    resolution = attrib(type=int, default=None, repr=False)

    intervalCounter = attrib(type=int, default=None, repr=False)

    shiftCounter = attrib(type=int, default=0, repr=False)


@attrs(eq=False)
class Unknown(object):

    index = attrib(type=int, default=0, repr=False)
    variable = attrib(type=ScalarVariable, default=None)
    dependencies = attrib(type=List[ScalarVariable], default=Factory(list), repr=False)
    dependenciesKind = attrib(type=List[str], default=Factory(list), repr=False)
    sourceline = attrib(type=int, default=0, repr=False)
    "Line number in the modelDescription.xml"


@attrs(eq=False)
class ModelDescription(object):

    guid = attrib(type=str, default=None, repr=False)
    fmiVersion = attrib(type=str, default=None)
    modelName = attrib(type=str, default=None)
    description = attrib(type=str, default=None, repr=False)
    generationTool = attrib(type=str, default=None, repr=False)
    generationDateAndTime = attrib(type=str, default=None, repr=False)
    variableNamingConvention = attrib(type=str, default='flat', repr=False)
    numberOfContinuousStates = attrib(type=int, default=0, repr=False)
    numberOfEventIndicators = attrib(type=int, default=0, repr=False)

    defaultExperiment = attrib(type=DefaultExperiment, default=None, repr=False)

    coSimulation = attrib(type=CoSimulation, default=None)
    modelExchange = attrib(type=ModelExchange, default=None)
    scheduledExecution = attrib(type=ScheduledExecution, default=None)

    buildConfigurations = attrib(type=List[BuildConfiguration], default=Factory(list), repr=False)

    unitDefinitions = attrib(type=List[Unit], default=Factory(list), repr=False)
    typeDefinitions = attrib(type=List[SimpleType], default=Factory(list), repr=False)
    modelVariables = attrib(type=List[ScalarVariable], default=Factory(list), repr=False)

    # model structure
    outputs = attrib(type=List[Unknown], default=Factory(list), repr=False)
    derivatives = attrib(type=List[Unknown], default=Factory(list), repr=False)
    clockedStates = attrib(type=List[Unknown], default=Factory(list), repr=False)
    eventIndicators = attrib(type=List[Unknown], default=Factory(list), repr=False)
    initialUnknowns = attrib(type=List[Unknown], default=Factory(list), repr=False)


class ValidationError(Exception):
    """ Exception raised for failed validation of the modelDescription.xml

    Attributes:
        problems    list of problems found
    """

    def __init__(self, problems):
        message = "Failed to validate modelDescription.xml:\n\n- " + '\n- '.join(problems)
        self.problems = problems
        super(ValidationError, self).__init__(message)


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

    if isinstance(filename, str) and os.path.isdir(filename):  # extracted FMU
        filename = os.path.join(filename, 'sources/buildDescription.xml')
        if not os.path.isfile(filename):
            return []
        tree = etree.parse(filename)
    elif isinstance(filename, str) and os.path.isfile(filename) and filename.lower().endswith('.xml'):  # XML file
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


def read_model_description(filename: Union[str, IO], validate: bool = True, validate_variable_names: bool = False, validate_model_structure: bool = False) -> ModelDescription:
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
    from . import validation
    import numpy as np

    # remember the original filename
    _filename = filename

    if isinstance(filename, str) and os.path.isdir(filename):  # extracted FMU
        filename = os.path.join(filename, 'modelDescription.xml')
        tree = etree.parse(filename)
    elif isinstance(filename, str) and os.path.isfile(filename) and filename.lower().endswith('.xml'):  # XML file
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
            problems = ["%s (line %d, column %d): %s" % (e.level_name, e.line, e.column, e.message)
                        for e in schema.error_log]
            raise ValidationError(problems)

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

    elif is_fmi3 and not (isinstance(filename, str) and _filename.endswith('.xml')):
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
        'fixed':      {'parameter': 'exact', 'calculatedParameter': 'calculated', 'structuralParameter': 'exact', 'local': 'calculated'},
        'tunable':    {'parameter': 'exact', 'calculatedParameter': 'calculated', 'structuralParameter': 'exact', 'local': 'calculated'},
        'discrete':   {'input': None, 'output': 'calculated', 'local': 'calculated'},
        'continuous': {'input': None, 'output': 'calculated', 'local': 'calculated', 'independent': None},
        'clock':      {'input': 'exact', 'output': 'calculated', 'local': 'calculated'},
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
            sv.intervalVariability = variable.get('intervalVariability')
            sv.clocks = variable.get('clocks')

        sv.type = value.tag

        if variable.tag in {'Binary', 'String'}:
            # handle <Start> element of Binary and String variables in FMI 3
            start = variable.find('Start')
            if start is not None:
                sv.start = start.get('value')
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
                              (modelDescription.derivatives, 'ContinuousStateDerivative'),
                              (modelDescription.clockedStates, 'ClockedState'),
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

        for variable in modelDescription.modelVariables:

            # resolve derivative
            if variable.derivative is not None:
                variable.derivative = variables[int(variable.derivative)]

            # resolve clocks
            if variable.clocks is not None:
                variable.clocks = [variables[int(vr)] for vr in variable.clocks.strip().split(' ')]

        # calculate numberOfContinuousStates
        for unknown in modelDescription.derivatives:
            modelDescription.numberOfContinuousStates += int(np.prod(unknown.variable.shape))

        # calculate numberOfEventIndicators
        for unknown in modelDescription.eventIndicators:
            modelDescription.numberOfEventIndicators += int(np.prod(unknown.variable.shape))

    if validate:
        problems = validation.validate_model_description(modelDescription,
                                                         validate_variable_names=validate_variable_names,
                                                         validate_model_structure=validate_model_structure)
        if problems:
            raise ValidationError(problems)

    return modelDescription
