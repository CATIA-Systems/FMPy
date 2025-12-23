""" Object model and loader for the modelDescription.xml """
from __future__ import annotations
from os import PathLike
from pathlib import Path

from typing import IO, Literal
from attrs import define, field, evolve


@define(eq=False)
class Category:

    name: str = None
    description: str | None = None


@define(eq=False)
class DefaultExperiment:

    startTime: str | None = None
    stopTime: str | None = None
    tolerance: str | None = None
    stepSize: str | None = None


@define(eq=False)
class InterfaceType:

    modelIdentifier: str | None = None
    needsExecutionTool: bool = field(default=False, repr=False)
    canBeInstantiatedOnlyOncePerProcess: bool = field(default=False, repr=False)
    canGetAndSetFMUState: bool = field(default=False, repr=False)
    canSerializeFMUState: bool = field(default=False, repr=False)
    providesDirectionalDerivative: bool = field(default=False, repr=False)
    providesAdjointDerivatives: bool = field(default=False, repr=False)
    providesPerElementDependencies: bool = field(default=False, repr=False)

    # for backwards compatibility
    # alias that delegates to the same attribute
    @property
    def canGetAndSetFMUstate(self) -> bool:
        return self.canGetAndSetFMUState

    @canGetAndSetFMUstate.setter
    def fullname(self, value: bool):
        self.canGetAndSetFMUState = value

    # FMI 2.0
    canNotUseMemoryManagementFunctions: bool = field(default=False, repr=False)
    providesDirectionalDerivative: bool = field(default=False, repr=False)


@define(eq=False)
class ModelExchange(InterfaceType):

    needsCompletedIntegratorStep: bool = field(default=False, repr=False)
    providesEvaluateDiscreteStates: bool = field(default=False, repr=False)


@define(eq=False)
class CoSimulation(InterfaceType):

    canHandleVariableCommunicationStepSize: bool = field(default=False, repr=False)
    fixedInternalStepSize: float | None = field(default=None, repr=False)
    maxOutputDerivativeOrder: int = field(default=0, repr=False)
    recommendedIntermediateInputSmoothness: int = field(default=0, repr=False)
    canInterpolateInputs: bool = field(default=False, repr=False)
    providesIntermediateUpdate: bool = field(default=False, repr=False)
    mightReturnEarlyFromDoStep: bool = field(default=False, repr=False)
    canReturnEarlyAfterIntermediateUpdate: bool = field(default=False, repr=False)
    hasEventMode: bool = field(default=False, repr=False)
    providesEvaluateDiscreteStates: bool = field(default=False, repr=False)

    # FMI 2.0
    canRunAsynchronuously: bool = field(default=False, repr=False)


@define(eq=False)
class ScheduledExecution(InterfaceType):
    ...


@define(eq=False)
class PreProcessorDefinition:

    name: str = None
    value: str = None
    optional: bool = False
    description: str = None


@define(eq=False)
class SourceFileSet:

    name: str = None
    language: str = None
    compiler: str = None
    compilerOptions: str = None
    preprocessorDefinitions: list[PreProcessorDefinition] = field(factory=list)
    sourceFiles: list[str] = field(factory=list)
    includeDirectories: list[str] = field(factory=list)


@define(eq=False)
class BuildConfiguration:

    modelIdentifier: str = None
    sourceFileSets: list[SourceFileSet] = field(factory=list)


@define(eq=False)
class Dimension:

    start: str
    valueReference: int
    variable: ModelVariable | None = None


@define(eq=False)
class Item:
    """ Enumeration Item """

    name: str | None = None
    value: str | None = None
    description: str | None = field(default=None, repr=False)


@define(eq=False)
class SimpleType:
    """ Type Definition """

    name: str | None = None
    description: str | None = None
    type: str | None = None
    quantity: str | None = field(default=None, repr=False)
    unit: str | None = None
    displayUnit: str | None = field(default=None, repr=False)
    relativeQuantity: str | None = field(default=None, repr=False)
    min: str | None = field(default=None, repr=False)
    max: str | None = field(default=None, repr=False)
    nominal: str | None = field(default=None, repr=False)
    unbounded: str | None = field(default=None, repr=False)
    items: list[Item] = field(factory=list, repr=False)


@define(eq=False)
class DisplayUnit:

    name: str | None = None
    factor: float = field(default=1.0, repr=False)
    offset: float = field(default=0.0, repr=False)


@define(eq=False)
class Unit:

    name: str | None = None
    baseUnit: BaseUnit | None = field(default=None, repr=False)
    displayUnits: list[DisplayUnit] = field(factory=list, repr=False)


@define(eq=False)
class BaseUnit:

    kg: int = 0
    m: int = 0
    s: int = 0
    A: int = 0
    K: int = 0
    mol: int = 0
    cd: int = 0
    rad: int = 0
    factor: float = 1.0
    offset: float = 0.0


@define(eq=False)
class VariableAlias:

    name: str
    description: str | None = field(default=None, repr=False)
    displayUnit: str | None = field(default=None, repr=False)


@define(eq=False)
class ModelVariable:

    name: str = field(default=None)

    valueReference: int = field(default=None, repr=False)

    type: Literal[
        'Real',
        'Float32',
        'Float64',
        'Integer',
        'Int8',
        'UInt8',
        'Int16',
        'UInt16',
        'Int32',
        'UInt32',
        'Int64',
        'UInt64',
        'Enumeration',
        'Boolean',
        'String',
        'Binary',
        'Clock',
    ] = field(default=None)

    shape: tuple[int, ...] | None = field(default=None, repr=False)

    _python_type = field(default=None, repr=False)

    description: str | None = field(default=None, repr=False)

    causality: Literal['parameter', 'calculatedParameter', 'input', 'output', 'local', 'independent', 'structuralParameter'] = field(default=None, repr=False)

    variability: Literal['constant', 'fixed', 'tunable', 'discrete', 'continuous'] = field(default=None, repr=False)

    initial: Literal['exact', 'approx', 'calculated', None] = field(default=None, repr=False)

    canHandleMultipleSetPerTimeInstant: bool = field(default=True, repr=False)

    intermediateUpdate: bool = field(default=False, repr=False)

    previous: int | None = field(default=None, repr=False)

    # TODO: resolve variables
    clocks: list[int] = field(factory=list, repr=False)

    declaredType: SimpleType | None = field(default=None, repr=False)

    dimensions: list[Dimension] = field(factory=list, repr=False)
    "List of fixed dimensions"

    dimensionValueReferences: list[int] = field(factory=list, repr=False)
    "List of value references to the variables that hold the dimensions"

    quantity: str | None = field(default=None, repr=False)
    "Physical quantity"

    unit: str | None = field(default=None, repr=False)
    "Unit"

    displayUnit: str | None = field(default=None, repr=False)
    "Default display unit"

    relativeQuantity: bool = field(default=False, repr=False)
    "Relative quantity"

    min: str | None = field(default=None, repr=False)
    "Minimum value"

    max: str | None = field(default=None, repr=False)
    "Maximum value"

    nominal: str | None = field(default=None, repr=False)
    "Nominal value"

    unbounded: bool = field(default=False, repr=False)
    "Value is unbounded"

    start: str | None = field(default=None, repr=False)
    "Initial or guess value"

    derivative: ModelVariable | None = field(default=None, repr=False)
    "The derivative of this variable"

    reinit: bool = field(default=False, repr=False)
    "Can be reinitialized at an event by the FMU"

    sourceline: int | None = field(default=None, repr=False)
    "Line number in the modelDescription.xml or None if unknown"

    # Clock attributes
    canBeDeactivated: bool = field(default=False, repr=False)

    priority: int | None = field(default=None, repr=False)

    intervalVariability: Literal['constant', 'fixed', 'tunable', 'changing', 'countdown', 'triggered', None] = field(default=None, repr=False)

    intervalDecimal: float | None = field(default=None, repr=False)

    shiftDecimal: float | None = field(default=None, repr=False)

    supportsFraction: bool = field(default=False, repr=False)

    resolution: int | None = field(default=None, repr=False)

    intervalCounter: int | None = field(default=None, repr=False)

    shiftCounter: int = field(default=0, repr=False)

    aliases: list[VariableAlias] = field(factory=list, repr=False)

    alias: ModelVariable | None = field(default=None, repr=False)


ScalarVariable = ModelVariable  # for backwards compatibility


@define(eq=False)
class Unknown:

    index: int = field(default=0, repr=False)
    variable: ModelVariable | None = None
    dependencies: list[ModelVariable] | None = field(default=None, repr=False)
    dependenciesKind: list[str] | None = field(default=None, repr=False)
    sourceline: int = field(default=0, repr=False)
    "Line number in the modelDescription.xml"


@define(eq=False)
class ModelDescription:

    fmiVersion: str | None = None
    modelName: str | None = None
    instantiationToken: str | None = field(default=None, repr=False)
    description: str | None = field(default=None, repr=False)
    author: str | None = field(default=None, repr=False)
    version: str | None = field(default=None, repr=False)
    copyright: str | None = field(default=None, repr=False)
    license: str | None = field(default=None, repr=False)
    generationTool: str | None = field(default=None, repr=False)
    generationDateAndTime: str | None = field(default=None, repr=False)
    variableNamingConvention: Literal['flat', 'structured'] = field(default='flat', repr=False)
    numberOfContinuousStates: int = field(default=0, repr=False)
    numberOfEventIndicators: int = field(default=0, repr=False)

    logCategories: list[Category] = field(factory=list, repr=False)

    defaultExperiment: DefaultExperiment = field(default=None, repr=False)

    coSimulation: CoSimulation | None = None
    modelExchange: ModelExchange | None = None
    scheduledExecution: ScheduledExecution | None = None

    buildConfigurations: list[BuildConfiguration] = field(factory=list, repr=False)

    unitDefinitions: list[Unit] = field(factory=list, repr=False)
    typeDefinitions: list[SimpleType] = field(factory=list, repr=False)
    modelVariables: list[ModelVariable] = field(factory=list, repr=False)

    # model structure
    outputs: list[Unknown] = field(factory=list, repr=False)
    derivatives: list[Unknown] = field(factory=list, repr=False)
    clockedStates: list[Unknown] = field(factory=list, repr=False)
    eventIndicators: list[Unknown] = field(factory=list, repr=False)
    initialUnknowns: list[Unknown] = field(factory=list, repr=False)

    @property
    def modelIdentifier(self) -> str:
        """Return the model identifier, if all model identifiers are equal"""

        model_identifiers = []

        if self.modelExchange:
            model_identifiers.append(self.modelExchange.modelIdentifier)
        if self.coSimulation:
            model_identifiers.append(self.coSimulation.modelIdentifier)
        if self.scheduledExecution:
            model_identifiers.append(self.scheduledExecution.modelIdentifier)

        if not model_identifiers:
            raise Exception("Model description does not define any model identifiers.")

        first = model_identifiers[0]

        if not all(first == i for i in model_identifiers):
            raise Exception("Model description defines different model identifiers.")

        return first

    @property
    def guid(self):
        return self.instantiationToken

    @guid.setter
    def guid(self, value):
        self.instantiationToken = value


class ValidationError(Exception):
    """ Exception raised for failed validation of the modelDescription.xml

    Attributes:
        problems    list of problems found
    """

    def __init__(self, problems):
        self.problems = problems

    def __str__(self):
        message = "Failed to validate modelDescription.xml:"
        for problem in self.problems:
            message += f"\n- {problem}"
        return message


def _copy_attributes(element, object, attributes=None):
    """ Copy attributes from an XML element to a Python object """

    if attributes is None:
        attributes = dir(object)

    for attribute in attributes:

        if attribute not in element.attrib:
            continue  # skip

        value = element.get(attribute)

        t = type(getattr(object, attribute))

        # convert the value to the correct type
        if t is bool:
            value = value in {'true', '1'}
        elif t is int:
            value = int(value)
        elif t is float:
            value = float(value)

        setattr(object, attribute, value)


def read_build_description(filename: str | PathLike | IO, validate=True) -> list[BuildConfiguration]:

    import zipfile
    from lxml import etree
    import os

    if isinstance(filename, (str, PathLike)) and os.path.isdir(filename):  # extracted FMU
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
                definition.optional = pd.get('optional') in {'true', '1'}
                definition.description = pd.get('description')
                sourceFileSet.preprocessorDefinitions.append(definition)

            for f in sf.findall('SourceFile'):
                sourceFileSet.sourceFiles.append(f.get('name'))

            for d in sf.findall('IncludeDirectory'):
                sourceFileSet.includeDirectories.append(d.get('name'))

            buildConfiguration.sourceFileSets.append(sourceFileSet)

    return build_configurations


def read_model_description(filename: str | PathLike | IO, validate: bool = True, validate_variable_names: bool = False, validate_model_structure: bool = False) -> ModelDescription:
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

    if isinstance(filename, (str, os.PathLike)) and os.path.isdir(filename):  # extracted FMU
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
    is_fmi3 = fmiVersion.startswith('3.')

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

    _copy_attributes(root, modelDescription, [
        'fmiVersion',
        'modelName',
        'guid',
        'description',
        'author',
        'version',
        'copyright',
        'license',
        'generationTool',
        'generationDateAndTime',
        'variableNamingConvention'])

    if is_fmi3:
        modelDescription.guid = root.get('instantiationToken')

    if root.get('numberOfEventIndicators') is not None:
        modelDescription.numberOfEventIndicators = int(root.get('numberOfEventIndicators'))

    if is_fmi1:
        modelDescription.numberOfContinuousStates = int(root.get('numberOfContinuousStates'))
    elif is_fmi2:
        modelDescription.numberOfContinuousStates = len(root.findall('ModelStructure/Derivatives/Unknown'))

    # log categories
    for l in root.findall('LogCategories/Category'):
        category = Category(name=l.get("name"), description=l.get("description"))
        modelDescription.logCategories.append(category)

    # default experiment
    for d in root.findall('DefaultExperiment'):
        modelDescription.defaultExperiment = DefaultExperiment(
            startTime=d.get("startTime"),
            stopTime=d.get("stopTime"),
            tolerance=d.get("tolerance"),
            stepSize=d.get("stepSize"),
        )

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
            modelDescription.modelExchange.needsCompletedIntegratorStep \
                = not me.get('completedIntegratorStepNotNeeded') in {'true', '1'}

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

        def get_fmu_state_attributes(element, object):
            object.canGetAndSetFMUState = element.get('canGetAndSetFMUState') in {'true', '1'}
            object.canSerializeFMUState = element.get('canSerializeFMUState') in {'true', '1'}

        for me in root.findall('ModelExchange'):
            modelDescription.modelExchange = ModelExchange()
            _copy_attributes(me, modelDescription.modelExchange)
            get_fmu_state_attributes(me, modelDescription.modelExchange)

        for cs in root.findall('CoSimulation'):
            modelDescription.coSimulation = CoSimulation()
            _copy_attributes(cs, modelDescription.coSimulation)
            get_fmu_state_attributes(cs, modelDescription.coSimulation)

        for se in root.findall('ScheduledExecution'):
            modelDescription.scheduledExecution = ScheduledExecution()
            _copy_attributes(se, modelDescription.scheduledExecution)
            get_fmu_state_attributes(se, modelDescription.scheduledExecution)

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

    elif is_fmi3 and not (isinstance(_filename, (str, PathLike)) and Path(_filename).name.endswith('.xml')):
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
                **dict(first.attrib)
            )

            # add enumeration items
            for i, item in enumerate(first.findall('Item')):
                it = Item(**item.attrib)
                if is_fmi1:
                    it.value = str(i + 1)
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

            simple_type = SimpleType(type=t.tag[:-4], **dict(t.attrib))

            # add enumeration items
            for item in t.findall('Item'):
                it = Item(**item.attrib)
                simple_type.items.append(it)

            modelDescription.typeDefinitions.append(simple_type)
            type_definitions[simple_type.name] = simple_type

    # default values for 'initial' derived from variability and causality
    initial_defaults = {
        'constant':   {'output': 'exact', 'local': 'exact'},
        'fixed':      {'structuralParameter': 'exact', 'parameter': 'exact', 'calculatedParameter': 'calculated', 'local': 'calculated'},
        'tunable':    {'structuralParameter': 'exact', 'parameter': 'exact', 'calculatedParameter': 'calculated', 'local': 'calculated'},
        'discrete':   {'input': 'exact', 'output': 'calculated', 'local': 'calculated'},
        'continuous': {'input': 'exact', 'output': 'calculated', 'local': 'calculated', 'independent': None},
    }

    # model variables
    for variable in root.find('ModelVariables'):

        if variable.get("name") is None:
            continue

        sv = ModelVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')), type=None)

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

        sv.description = variable.get('description')
        sv.causality = variable.get('causality', default='local')
        sv.variability = variable.get('variability')
        sv.initial = variable.get('initial')
        sv.sourceline = variable.sourceline

        if variable.tag in {'Binary', 'String'}:
            # handle <Start> element of Binary and String variables in FMI 3
            start = variable.find('Start')
            if start is not None:
                sv.start = start.get('value')
        else:
            sv.start = value.get('start')

        # add variable aliases
        for alias in filter(lambda child: getattr(child, 'tag') == 'Alias', variable):
            sv.aliases.append(VariableAlias(
                name=alias.get('name'),
                description=alias.get('description'),
                displayUnit=alias.get('displayUnit')
            ))

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
            'Binary':      bytes.fromhex,
            'Clock':       float,
        }

        sv._python_type = type_map[sv.type]

        if sv.type in ['Real', 'Float32', 'Float64']:
            sv.unit = value.get('unit')
            sv.displayUnit = value.get('displayUnit')
            sv.relativeQuantity = value.get('relativeQuantity') in {'true', '1'}
            sv.derivative = value.get('derivative')
            sv.nominal = value.get('nominal')
            sv.unbounded = value.get('unbounded') in {'true', '1'}

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
                sv.variability = 'fixed'

        if sv.variability is None:
            if is_fmi1 or is_fmi2:
                sv.variability = 'continuous'
            else:
                if sv.causality in {'parameter', 'calculatedParameter', 'structuralParameter'}:
                    sv.variability = 'fixed'
                elif sv.type in {'Float32', 'Float64'} and sv.causality not in {'parameter', 'structuralParameter', 'calculatedParameter'}:
                    sv.variability = 'continuous'
                else:
                    sv.variability = 'discrete'

        if sv.initial is None and not is_fmi1:
            try:
                sv.initial = initial_defaults[sv.variability][sv.causality]
            except KeyError:
                raise Exception(f'Variable "{sv.name}" (line {sv.sourceline}) has an illegal combination of '
                                f'causality="{sv.causality}" and variability="{sv.variability}".')

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

    # resolve dimension variables and calculate initial shape
    for variable in modelDescription.modelVariables:

        shape = []

        for dimension in variable.dimensions:

            if dimension.start is not None:
                shape.append(int(dimension.start))
            else:
                dimension.variable = variables[dimension.valueReference]
                shape.append(int(dimension.variable.start))

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
                index = int(variable.derivative)
                if index == 0 or index > len(modelDescription.modelVariables):
                    message = f"The derivative attribute of model variable {variable.name} (line {variable.sourceline}) references model variable index {index} which does not exist."
                    raise ValidationError(problems=[message])
                variable.derivative = modelDescription.modelVariables[index - 1]

    if is_fmi3:

        alias_variables = []

        for variable in modelDescription.modelVariables:
            for alias in variable.aliases:
                alias_variable = evolve(variable, name=alias.name, alias=variable)
                if alias.description:
                    alias_variable.description = alias.description
                if alias.displayUnit:
                    alias_variable.displayUnit = alias.displayUnit
                alias_variables.append(alias_variable)

        modelDescription.modelVariables += alias_variables

        for attr, element in [(modelDescription.outputs, 'Output'),
                              (modelDescription.derivatives, 'ContinuousStateDerivative'),
                              (modelDescription.clockedStates, 'ClockedState'),
                              (modelDescription.initialUnknowns, 'InitialUnknown'),
                              (modelDescription.eventIndicators, 'EventIndicator')]:

            for u in root.findall('ModelStructure/' + element):
                unknown = Unknown()
                unknown.sourceline = u.sourceline
                unknown.variable = variables[int(u.get('valueReference'))]

                if "dependencies" in u.attrib:
                    dependencies = u.get('dependencies').strip()
                    if len(dependencies) == 0:
                        unknown.dependencies = []
                    else:
                        unknown.dependencies = list(map(lambda vr: variables[int(vr)], dependencies.split(' ')))

                if "dependenciesKind" in u.attrib:
                    dependenciesKind = u.get('dependenciesKind').strip()
                    if len(dependenciesKind) == 0:
                        unknown.dependenciesKind = []
                    else:
                        unknown.dependenciesKind = dependenciesKind.split(' ')

                attr.append(unknown)

        for variable in modelDescription.modelVariables:

            # resolve derivative
            if variable.derivative is not None:
                vr = int(variable.derivative)
                if vr not in variables:
                    message = f"The derivative attribute of model variable {variable.name} (line {variable.sourceline}) references value reference {vr} which does not exist."
                    raise ValidationError(problems=[message])
                variable.derivative = variables[vr]

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


def _write_fmi3_model_description(model_description: ModelDescription, path: Path):

    from lxml.etree import ElementTree, Element, SubElement

    def to_literal(value):
        if value is None:
            return None
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def set_attributes(element, object, attributes):
        for attribute_name, default_value in attributes:
            value = getattr(object, attribute_name)
            if value != default_value:
                element.set(attribute_name, to_literal(value))

    root = Element("fmiModelDescription")

    # basic attributes
    for attr in (
        "fmiVersion",
        "modelName",
        "instantiationToken",
        "description",
        "author",
        "version",
        "copyright",
        "license",
        "generationTool",
        "generationDateAndTime",
        "variableNamingConvention",
    ):
        val = getattr(model_description, attr, None)
        if val is not None:
            root.set(attr, to_literal(val))

    implementation_attributes = [
        ("modelIdentifier", None),
        ("needsExecutionTool", False),
        ("canBeInstantiatedOnlyOncePerProcess", False),
        ("canGetAndSetFMUState", False),
        ("canSerializeFMUState", False),
        ("providesDirectionalDerivative", False),
        ("providesAdjointDerivatives", False),
        ("providesPerElementDependencies", False),
    ]

    if model_description.modelExchange is not None:
        from lxml.etree import SubElement
        ModelExchange = SubElement(root, "ModelExchange")
        set_attributes(ModelExchange, model_description.modelExchange, implementation_attributes + [
            ("needsCompletedIntegratorStep", False),
            ("providesEvaluateDiscreteStates", False),
        ])

    if model_description.modelExchange is not None:
        CoSimulation = SubElement(root, "CoSimulation")
        set_attributes(CoSimulation, model_description.coSimulation, implementation_attributes + [
            ("canHandleVariableCommunicationStepSize", False),
            ("fixedInternalStepSize", None),
            ("maxOutputDerivativeOrder", False),
            ("recommendedIntermediateInputSmoothness", False),
            ("canInterpolateInputs", False),
            ("providesIntermediateUpdate", False),
            ("mightReturnEarlyFromDoStep", False),
            ("canReturnEarlyAfterIntermediateUpdate", False),
            ("hasEventMode", False),
            ("providesEvaluateDiscreteStates", False),
        ])

    if model_description.unitDefinitions:
        UnitDefinitions = SubElement(root, "UnitDefinitions")
        for unit in model_description.unitDefinitions:
            Unit = SubElement(UnitDefinitions, "Unit")
            Unit.set("name", unit.name)
            BaseUnit = SubElement(Unit, "BaseUnit")
            set_attributes(
                BaseUnit,
                unit.baseUnit,
                [
                    ("kg", 0),
                    ("m", 0),
                    ("s", 0),
                    ("A", 0),
                    ("K", 0),
                    ("mol", 0),
                    ("cd", 0),
                    ("rad", 0),
                    ("factor", 1.0),
                    ("offset", 0.0),
                ],
            )
            for display_unit in unit.displayUnits:
                DisplayUnit = SubElement(Unit, "DisplayUnit")
                set_attributes(DisplayUnit, display_unit, [("name", None), ("factor", 1.0), ("offset", 0.0)])

    if model_description.typeDefinitions:
        TypeDefintions = SubElement(root, "TypeDefinitions")
        for type_defintion in model_description.typeDefinitions:
            TypeDefinition = SubElement(
                TypeDefintions, type_defintion.type + "Type"
            )
            set_attributes(
                TypeDefinition,
                type_defintion,
                [
                    ("name", None),
                    ("description", None),
                    ("quantity", None),
                    ("unit", None),
                    ("displayUnit", None),
                    ("relativeQuantity", None),
                    ("min", None),
                    ("max", None),
                    ("nominal", None),
                    ("nominal", None),
                    ("unbounded", None),
                ],
            )

    if model_description.logCategories:
        LogCategories = SubElement(root, "LogCategories")
        for category in model_description.logCategories:
            Category = SubElement(LogCategories, "Category")
            set_attributes(Category, category, [("name", None), ("description", None)])

    if model_description.defaultExperiment is not None:
        DefaultExperiment = SubElement(root, "DefaultExperiment")
        set_attributes(DefaultExperiment, model_description.defaultExperiment, [("startTime", None), ("stopTime", None), ("stepSize", None)])

    ModelVariables = SubElement(root, "ModelVariables")

    for variable in model_description.modelVariables:
        if variable.alias is not None:
            continue

        ModelVariable = SubElement(ModelVariables, variable.type)

        set_attributes(
            ModelVariable,
            variable,
            [
                ("name", None),
                ("valueReference", None),
                ("causality", None),
                ("start", None),
                ("variability", None),
                ("initial", None),
                ("declaredType", None),
                ("derivative", None),
                ("description", None),
            ],
        )

        if variable.derivative is not None:
            ModelVariable.set("derivative", str(variable.derivative.valueReference))

        if variable.declaredType is not None:
            ModelVariable.set("declaredType", variable.declaredType.name)

        for alias in variable.aliases:
            Alias = SubElement(ModelVariable, "Alias")
            Alias.set("name", alias.name)
            Alias.set("description", alias.description)
            Alias.set("displayUnit", alias.displayUnit)

    ModelStructure = SubElement(root, "ModelStructure")

    for element_name, unknowns in [
        ("Output", model_description.outputs),
        ("ContinuousStateDerivative", model_description.derivatives),
        ("InitialUnknown", model_description.initialUnknowns),
        ("EventIndicator", model_description.eventIndicators),
    ]:
        for unknown in unknowns:
            Unknown = SubElement(ModelStructure, element_name)
            Unknown.set("valueReference", str(unknown.variable.valueReference))
            if unknown.dependencies is not None:
                Unknown.set(
                    "dependencies",
                    " ".join(
                        map(lambda v: str(v.valueReference), unknown.dependencies)
                    ),
                )
            if unknown.dependenciesKind is not None:
                Unknown.set("dependenciesKind", " ".join(unknown.dependenciesKind))

    tree = ElementTree(root)

    tree.write(path, encoding="utf-8", xml_declaration=True, pretty_print=True)


def write_model_description(model_description: ModelDescription, path: Path):
    _write_fmi3_model_description(model_description, path)