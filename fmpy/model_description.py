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

        self.buildConfigurations = []

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

        self.dimensions = None
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


def read_model_description(filename, validate=True, validate_variable_names=False):
    """ Read the model description from an FMU without extracting it

    Parameters:
        filename                 filename of the FMU or XML file, directory with extracted FMU or file like object
        validate                 whether the model description should be validated
        validate_variable_names  validate the variable names against the EBNF

    returns:
        model_description   a ModelDescription object
    """

    import zipfile
    from lxml import etree
    import os
    from .util import _is_string

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

    if not fmiVersion.startswith('3.0') and fmiVersion not in ['1.0', '2.0']:
        raise Exception("Unsupported FMI version: %s" % fmiVersion)

    if validate:

        module_dir, _ = os.path.split(__file__)

        if fmiVersion == '1.0':
            schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', 'fmi1', 'fmiModelDescription.xsd'))
        elif fmiVersion == '2.0':
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

    if fmiVersion.startswith('3.0'):
        modelDescription.guid = root.get('instantiationToken')

    if root.get('numberOfEventIndicators') is not None:
        modelDescription.numberOfEventIndicators = int(root.get('numberOfEventIndicators'))

    if fmiVersion == '1.0':
        modelDescription.numberOfContinuousStates = int(root.get('numberOfContinuousStates'))
    elif fmiVersion == '2.0':
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

    # build configurations
    if fmiVersion == '2.0':

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

    elif fmiVersion.startswith('3.0'):

        for bc in root.findall('BuildConfiguration'):

            buildConfiguration = BuildConfiguration()
            buildConfiguration.modelIdentifier = bc.get('modelIdentifier')

            modelDescription.buildConfigurations.append(buildConfiguration)

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

    # unit definitions
    if fmiVersion == '1.0':

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

    # FMI 1 and 2
    for t in root.findall('TypeDefinitions/' + ('Type' if fmiVersion == '1.0' else 'SimpleType')):

        first = t[0]  # first element

        simple_type = SimpleType(
            name=t.get('name'),
            type=first.tag[:-len('Type')] if fmiVersion == '1.0' else first.tag,
            **first.attrib
        )

        # add enumeration items
        for i, item in enumerate(first.findall('Item')):
            it = Item(**item.attrib)
            if fmiVersion == '1.0':
                it.value = i + 1
            simple_type.items.append(it)

        modelDescription.typeDefinitions.append(simple_type)
        type_definitions[simple_type.name] = simple_type

    # FMI 3
    for t in root.findall('TypeDefinitions/*'):

        if t.tag not in {'Float32', 'Float64', 'Int8', 'UInt8', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Int64', 'UInt64',
                         'Boolean', 'String', 'Binary', 'Enumeration'}:
            continue

        simple_type = SimpleType(type=t.tag, **t.attrib)

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
        'clock':      {'inferred': None, 'triggered': None},
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
        sv.sourceline = variable.sourceline

        if fmiVersion in ['1.0', '2.0']:
            # get the "value" element
            for child in variable.iterchildren():
                if child.tag in {'Real', 'Integer', 'Boolean', 'String', 'Enumeration'}:
                    value = child
                    break
        else:
            value = variable

        sv.type = value.tag
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

        if sv.type == 'Real':
            sv.unit = value.get('unit')
            sv.displayUnit = value.get('displayUnit')
            sv.relativeQuantity = value.get('relativeQuantity') == 'true'
            sv.derivative = value.get('derivative')
            sv.nominal = value.get('nominal')
            sv.unbounded = value.get('unbounded') == 'true'

        if sv.type in ['Real', 'Integer', 'Enumeration']:
            sv.quantity = value.get('quantity')
            sv.min = value.get('min')
            sv.max = value.get('max')

        # resolve the declared type
        sv.declaredType = type_definitions[value.get('declaredType')]

        if fmiVersion == '1.0':
            if sv.causality == 'internal':
                sv.causality = 'local'

            if sv.variability == 'parameter':
                sv.causality = 'parameter'
                sv.variability = None
        else:
            if sv.variability is None:
                sv.variability = 'continuous' if sv.type in {'Float32', 'Float64', 'Real'} else 'discrete'

            if sv.initial is None:
                sv.initial = initial_defaults[sv.variability][sv.causality]

        dimensions = variable.findall('Dimension')

        if dimensions:
            sv.dimensions = []
            for dimension in dimensions:
                start = dimension.get('start')
                sv.dimensions.append(int(start) if start is not None else None)
                vr = dimension.get('valueReference')
                sv.dimensionValueReferences.append(int(vr) if vr is not None else None)

        modelDescription.modelVariables.append(sv)

    # variables = dict((v.valueReference, v) for v in modelDescription.modelVariables)
    #
    # resolve dimensions and calculate extent
    # for variable in modelDescription.modelVariables:
    #     variable.dimensions = list(map(lambda vr: variables[vr], variable.dimensions))
    #     variable.extent = tuple(map(lambda d: int(d.start), variable.dimensions))

    if fmiVersion == '2.0':

        # model structure
        for attr, element in [(modelDescription.outputs, 'Outputs'),
                              (modelDescription.derivatives, 'Derivatives'),
                              (modelDescription.initialUnknowns, 'InitialUnknowns')]:

            for u in root.findall('ModelStructure/' + element + '/Unknown'):
                unknown = Unknown()

                unknown.variable = modelDescription.modelVariables[int(u.get('index')) - 1]

                dependencies = u.get('dependencies')

                if dependencies:
                    for vr in dependencies.strip().split(' '):
                        unknown.dependencies.append(modelDescription.modelVariables[int(vr) - 1])

                dependenciesKind = u.get('dependenciesKind')

                if dependenciesKind:
                    unknown.dependenciesKind = dependenciesKind.strip().split(' ')

                attr.append(unknown)

    if validate:

        # assert attribute "derivative" for derivatives defined in <ModelStructure>
        for i, derivative in enumerate(modelDescription.derivatives):
            if derivative.variable.derivative is None:
                raise Exception('State variable "%s" (line %s, state index %d) does not define a derivative.' % (derivative.variable.name, derivative.variable.sourceline, i + 1))

        unit_definitions = {}

        for unit in modelDescription.unitDefinitions:
            unit_definitions[unit.name] = [display_unit.name for display_unit in unit.displayUnits]

        variable_names = set()

        # assert unique variable names (FMI 1.0 spec, p. 34, FMI 2.0 spec, p. 45)
        for variable in modelDescription.modelVariables:
            if variable.name in variable_names:
                raise Exception('Variable name "%s" (line %s) is not unique.' % (variable.name, variable.sourceline))
            variable_names.add(variable.name)

        if modelDescription.fmiVersion == '2.0':

            # assert required start values (see FMI 2.0 spec, p. 47)
            for variable in modelDescription.modelVariables:
                if (variable.initial in {'exact', 'approx'} or variable.causality == 'input') and variable.start is None:
                    raise Exception('Variable "%s" (line %s) has no start value.' % (variable.name, variable.sourceline))

            # legal combinations of causality and variability (see FMI 2.0 spec, p. 49)
            legal_combinations = {
                ('parameter', 'fixed'),
                ('parameter', 'tunable'),
                ('calculatedParameter', 'fixed'),
                ('calculatedParameter', 'tunable'),
                ('input', 'discrete'),
                ('input', 'continuous'),
                ('output', 'constant'),
                ('output', 'discrete'),
                ('output', 'continuous'),
                ('local', 'constant'),
                ('local', 'fixed'),
                ('local', 'tunable'),
                ('local', 'discrete'),
                ('local', 'continuous'),
                ('independent', 'continuous'),
            }

            for variable in modelDescription.modelVariables:
                if (variable.causality, variable.variability) not in legal_combinations:
                    raise Exception('The combination causlity="%s" and variability="%s" in variable "%s" (line %s) is not allowed.'
                                    % (variable.causality, variable.variability, variable.name, variable.sourceline))

            # check required start values
            for variable in modelDescription.modelVariables:
                if (variable.initial in {'exact', 'approx'} or variable.causality == 'input') and variable.start is None:
                    raise Exception('Variable "%s" (line %s) has no start value.' % (variable.sourceline, variable.name))

            # validate outputs
            outputs = set([v for v in modelDescription.modelVariables if v.causality == 'output'])
            unknowns = set([u.variable for u in modelDescription.outputs])

            if outputs != unknowns:
                raise Exception('ModelStructure/Outputs must have exactly one entry for each variable with causality="output".')

            # validate units
            for variable in modelDescription.modelVariables:

                unit = variable.unit

                if unit is None and variable.declaredType is not None:
                    unit = variable.declaredType.unit

                if unit is not None and unit not in unit_definitions:
                    raise Exception('The unit "%s" of variable "%s" (line %s) is not defined.' % (unit, variable.name, variable.sourceline))

                if variable.displayUnit is not None and variable.displayUnit not in unit_definitions[unit]:
                    raise Exception('The display unit "%s" of variable "%s" (line %s) is not defined.' % (variable.displayUnit, variable.name, variable.sourceline))

    if validate_variable_names:

        if modelDescription.variableNamingConvention == 'flat':

            for variable in modelDescription.modelVariables:

                if u'\u000D' in variable.name:
                    raise Exception('Variable "%s" (line %s) contains an illegal carriage return character (U+000D).'
                                    % (variable.name, variable.sourceline))

                if u'\u000A' in variable.name:
                    raise Exception('Variable "%s" (line %s) contains an illegal line feed character (U+000A).'
                                    % (variable.name, variable.sourceline))

                if u'\u0009' in variable.name:
                    raise Exception('Variable "%s" (line %s) contains an illegal tab character (U+0009).'
                                    % (variable.name, variable.sourceline))

        else:  # variableNamingConvention == structured

            from lark import Lark

            grammar = r"""
                name            : identifier | "der(" identifier ("," unsignedinteger)? ")"
                identifier      : bname arrayindices? ("." bname arrayindices?)*
                bname           : nondigit (nondigit|digit)* | qname
                nondigit        : "_" | "a".."z" | "A".."Z"
                digit           : "0".."9"
                qname           : "'" ( qchar | escape ) ( qchar | escape ) "'"
                qchar           : nondigit | digit | "!" | "#" | "$" | "%" | "&" | "(" | ")" 
                                  | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | "<" | ">"
                                  | "=" | "?" | "@" | "[" | "]" | "^" | "{" | "}" | "|" | "~" | " "
                escape          : "\'" | "\"" | "\?" | "\\" | "\a" | "\b" | "\f" | "\n" | "\r" | "\t" | "\v"
                arrayindices    : "[" unsignedinteger ("," unsignedinteger)* "]"
                unsignedinteger : digit+
                """

            parser = Lark(grammar, start='name')

            try:
                for variable in modelDescription.modelVariables:
                    parser.parse(variable.name)
            except Exception as e:
                raise Exception('"%s" (line %s) is not a legal variable name for naming convention "structured". %s'
                                % (variable.name, variable.sourceline, e))

    return modelDescription
