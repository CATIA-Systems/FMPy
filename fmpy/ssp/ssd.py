from lxml import etree
import zipfile
import os

# namespaces for XML parsing
ns = {
    'ssc': 'http://www.pmsf.net/xsd/SystemStructureCommonDraft',
    'ssd': 'http://www.pmsf.net/xsd/SystemStructureDescriptionDraft',
    'ssm': 'http://www.pmsf.net/xsd/SystemStructureParameterMappingDraft',
    'ssv': 'http://www.pmsf.net/xsd/SystemStructureParameterValuesDraft',
    'sss': 'http://www.pmsf.net/xsd/SystemStructureSignalDictionaryDraft',
}


# common
class BaseElement(object):

    def __init__(self, **kwargs):
        super(BaseElement, self).__init__()
        self.id = kwargs.get('id', None)
        self.description = kwargs.get('description', None)


class TopLevelMetaData(object):

    def __init__(self, **kwargs):
        super(TopLevelMetaData, self).__init__()
        self.author = kwargs.get('author', None)
        self.fileversion = kwargs.get('fileversion', None)
        self.copyright = kwargs.get('copyright', None)
        self.license = kwargs.get('license', None)
        self.generationTool = kwargs.get('generationTool', None)
        self.generationDateAndTime = kwargs.get('generationDateAndTime', None)


class LinearTransformation(object):

    def __init__(self, factor=1.0, offset=0.0):
        super(LinearTransformation, self).__init__()
        self.factor = factor
        self.offset = offset

    def __repr__(self):
        return "LinearTransformation (factor: %s, offset: %s)" % (self.factor, self.offset)


class BooleanMappingTransformation(object):

    def __init__(self):
        super(BooleanMappingTransformation, self).__init__()
        self.entries = {}

    def __repr__(self):
        return "BooleanMappingTransformation (entries: %s)" % (self.entries,)


class IntegerMappingTransformation(object):

    def __init__(self):
        super(IntegerMappingTransformation, self).__init__()
        self.entries = {}

    def __repr__(self):
        return "IntegerMappingTransformation (entries: %s)" % (self.entries,)


class EnumerationMappingTransformation(object):

    def __init__(self):
        super(EnumerationMappingTransformation, self).__init__()
        self.entries = {}

    def __repr__(self):
        return "EnumerationMappingTransformation (entries: %s)" % (self.entries,)


# system structure description
class SystemStructureDescription(BaseElement, TopLevelMetaData):

    def __init__(self, **kwargs):
        super(SystemStructureDescription, self).__init__(**kwargs)
        self.system = kwargs.get('system')
        self.enumerations = kwargs.get('enumerations', [])
        self.units = kwargs.get('units', [])
        self.defaultExperiment = kwargs.get('defaultExperiment')
        self.annotations = kwargs.get('annotations', [])
        self.version = kwargs.get('version')
        self.name = kwargs.get('name')

    def __repr__(self):
        return "SystemStructureDescription (name: %s)" % self.name


class Element(BaseElement):

    def __init__(self, **kwargs):
        super(Element, self).__init__(**kwargs)
        self.connectors = kwargs.get('connectors', [])
        self.parameterBindings = kwargs.get('parameterBindings', [])
        self.name = kwargs.get('name')


class Component(Element):

    def __init__(self, **kwargs):
        super(Component, self).__init__(**kwargs)
        self.type = kwargs.get('type')
        self.source = kwargs.get('source')
        self.implementation = kwargs.get('implementation')

    def __repr__(self):
        return "Component (name: %s, source: %s, type: %s)" % (self.name, self.source, self.type)


class System(Element):

    def __init__(self, **kwargs):
        super(System, self).__init__(**kwargs)
        self.elements = kwargs.get('elements', [])
        self.connections = kwargs.get('connections', [])
        self.signalDictionaries = kwargs.get('signalDictionaries', [])
        self.systemGeometry = kwargs.get('systemGeometry')
        self.graphicalElements = kwargs.get('graphicalElements', [])
        self.simulationInformation = kwargs.get('simulationInformation')
        self.annotations = kwargs.get('annotations', [])

    def __repr__(self):
        return "System (name: %s, description: %s)" % (self.name, self.description)


class Connector(BaseElement):

    def __init__(self, **kwargs):
        super(Connector, self).__init__(**kwargs)
        self.name = kwargs.get('name')
        self.kind = kwargs.get('kind')

    def __repr__(self):
        return "Connector (name: %s, kind: %s)" % (self.name, self.kind)


class Connection(BaseElement):

    def __init__(self, **kwargs):
        super(Connection, self).__init__(**kwargs)
        self.startElement = kwargs.get('startElement')
        self.startConnector = kwargs.get('startConnector')
        self.endElement = kwargs.get('endElement')
        self.endConnector = kwargs.get('endConnector')

    def __repr__(self):
        return "Connection (startElement: %s, startConnector: %s, endElement: %s, endConnector: %s)" % (self.startElement, self.startConnector, self.endElement, self.endConnector)


class ParameterBinding(BaseElement):

    def __init__(self, **kwargs):
        super(ParameterBinding, self).__init__(**kwargs)
        self.parameterValues = kwargs.get('parameterValues', [])
        self.parameterMapping = kwargs.get('parameterMapping', [])
        self.annotations = kwargs.get('annotations', [])
        self.type = kwargs.get('type')
        self.source = kwargs.get('source')
        self.sourceBase = kwargs.get('sourceBase')
        self.prefix = kwargs.get('prefix')

    def __repr__(self):
        return "ParameterBinding (prefix: %s, source: %s, type: %s)" % (self.prefix, self.source, self.type)


class DefaultExperiment(object):

    def __init__(self):
        super(DefaultExperiment, self).__init__()
        self.annotations = []
        self.startTime = None
        self.stopTime = None


class SimulationInformation(object):

    def __init__(self, **kwargs):
        super(SimulationInformation, self).__init__()
        self.fixedStepSolver = kwargs.get('fixedStepSolver')
        self.variableStepSolver = kwargs.get('variableStepSolver')
        self.fixedStepMaster = kwargs.get('fixedStepMaster')
        self.variableStepMaster = kwargs.get('variableStepMaster')
        self.annotations = kwargs.get('annotations', [])


class FixedStepSolver(object):

    def __init__(self, **kwargs):
        super(FixedStepSolver, self).__init__()
        self.description = kwargs.get('description')
        self.stepSize = kwargs.get('stepSize')


class VariableStepSolver(object):

    def __init__(self, **kwargs):
        super(VariableStepSolver, self).__init__()
        self.description = kwargs.get('description')
        self.absoluteTolerance = kwargs.get('absoluteTolerance')
        self.relativeTolerance = kwargs.get('relativeTolerance')
        self.minimumStepSize = kwargs.get('minimumStepSize')
        self.maximumStepSize = kwargs.get('maximumStepSize')
        self.initialStepSize = kwargs.get('initialStepSize')


class FixedStepMaster(object):

    def __init__(self, **kwargs):
        super(FixedStepMaster, self).__init__()
        self.description = kwargs.get('description')
        self.stepSize = kwargs.get('stepSize')


class VariableStepMaster(object):

    def __init__(self, **kwargs):
        super(VariableStepMaster, self).__init__()
        self.description = kwargs.get('description')
        self.minimumStepSize = kwargs.get('minimumStepSize')
        self.maximumStepSize = kwargs.get('maximumStepSize')
        self.initialStepSize = kwargs.get('initialStepSize')


# parameter mapping
class ParameterMapping(BaseElement, TopLevelMetaData):

    def __init__(self, **kwargs):
        super(ParameterMapping, self).__init__(**kwargs)
        self.mappingEntries = kwargs.get('mappingEntries', [])
        self.annotations = kwargs.get('annotations', [])
        self.version = kwargs.get('version')


class MappingEntry(BaseElement):

    def __init__(self, **kwargs):
        super(MappingEntry, self).__init__(**kwargs)
        self.transformation = kwargs.get('transformation')
        self.source = kwargs.get('source')
        self.target = kwargs.get('target')
        self.suppressUnitConversion = kwargs.get('suppressUnitConversion')


class SignalDictionaryReference(object):

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.dictionary = kwargs.get('dictionary')
        self.connectors = kwargs.get('connectors', [])

    def __repr__(self):
        return "SignalDictionaryReference (name: %s, dictionary: %s)" % (self.name, self.dictionary)


# signal dictionary
class SignalDictionary(BaseElement, TopLevelMetaData):

    def __init__(self, **kwargs):
        super(SignalDictionary, self).__init__(**kwargs)
        self.entries = kwargs.get('entries', [])
        self.enumerations = kwargs.get('enumerations', [])
        self.units = kwargs.get('units', [])
        self.annotations = kwargs.get('annotations', [])
        self.version = kwargs.get('version')
        self.type = kwargs.get('type')
        self.source = kwargs.get('source')
        self.name = kwargs.get('name')

    def __repr__(self):
        return "SignalDictionary"


class DictionaryEntry(BaseElement):

    def __init__(self, **kwargs):
        super(DictionaryEntry, self).__init__(**kwargs)
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        self.unit = kwargs.get('unit')

    def __repr__(self):
        return "DictionaryEntry (name: %s, type: %s, unit=%s)" % (self.name, self.type, self.unit)


class Unit(object):

    def __init__(self, **kwargs):
        super(Unit, self).__init__()
        self.name = kwargs.get('name')
        self.kg = int(kwargs.get('kg', 0))
        self.m = int(kwargs.get('m', 0))
        self.s = int(kwargs.get('s', 0))
        self.A = int(kwargs.get('A', 0))
        self.K = int(kwargs.get('K', 0))
        self.mol = int(kwargs.get('mol', 0))
        self.cd = int(kwargs.get('cd', 0))
        self.rad = int(kwargs.get('rad', 0))
        self.factor = float(kwargs.get('factor', 1.0))
        self.offset = float(kwargs.get('offset', 0.0))

    def __repr__(self):
        return "Unit (name: %s, kg: %d, m: %d, s: %d, A: %d, K: %d, mol: %d, cd: %d, rad: %d, factor: %g, offset: %g)" % (self.name, self.kg, self.m, self.s, self.A, self.K, self.mol, self.cd, self.rad, self.factor, self.offset)


class ParameterSet(BaseElement, TopLevelMetaData):

    def __init__(self, **kwargs):
        super(ParameterSet, self).__init__(**kwargs)
        self.parameters = kwargs.get('parameters', [])
        self.enumerations = kwargs.get('enumerations', [])
        self.units = kwargs.get('units', [])
        self.annotations = kwargs.get('annotations', [])
        self.version = kwargs.get('version')
        self.name = kwargs.get('name')

    def __repr__(self):
        return "ParameterSet (name: %s)" % self.name


class Parameter(BaseElement):

    def __init__(self, **kwargs):
        super(Parameter, self).__init__()
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        self.value = kwargs.get('value')
        self.unit = kwargs.get('unit')

    def __repr__(self):
        return "Parameter (name: %s, type: %s, value: %s, unit: %s)" % (self.name, self.type, self.value, self.unit)


def validate_tree(root, schema_file):

    module_dir, _ = os.path.split(__file__)

    schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', schema_file))

    if not schema.validate(root):
        message = "Failed to validate SystemStructure.ssd:"
        for entry in schema.error_log:
            message += "\n%s (line %d, column %d): %s" % (entry.level_name, entry.line, entry.column, entry.message)
        raise Exception(message)


def read_ssv(filename, resource=None, validate=True):

    if resource is None:
        tree = etree.parse(filename)
    else:
        # load parameter set
        with zipfile.ZipFile(filename, 'r') as zf:
            xml = zf.open(resource)
            tree = etree.parse(xml)

    root = tree.getroot()

    if validate:
        validate_tree(root, 'SystemStructureParameterValues.xsd')

    return _get_parameter_set(root)


def _get_transformation(element):

    for t in element.findall('ssc:LinearTransformation', namespaces=ns):
        return LinearTransformation(**t.attrib)

    # TODO:
    # for type in [BooleanMappingTransformation, IntegerMappingTransformation, EnumerationMappingTransformation]:
    #     pass

    return None


def _get_parameter_set(element):

    parameter_set = ParameterSet(name=element.get('name'))

    for p in element.findall('ssv:Parameters/ssv:Parameter', namespaces=ns):

        parameter = Parameter(name=p.get('name'))
        real = p.find('ssv:Real', namespaces=ns)

        if real is not None:
            parameter.type = 'Real'
            parameter.value = real.get('value')
            parameter.unit = real.get('unit')
        else:
            for type in ['Integer', 'Boolean', 'String', 'Enumeration', 'Binary']:
                entry = p.find('ssv:' + type, namespaces=ns)
                if entry is not None:
                    parameter.type = type
                    parameter.value = entry.get('value')
                    break

        parameter_set.parameters.append(parameter)

    return parameter_set


def read_ssm(filename, resource=None, validate=True):

    if resource is None:
        tree = etree.parse(filename)
    else:
        # load parameter set
        with zipfile.ZipFile(filename, 'r') as zf:
            xml = zf.open(resource)
            tree = etree.parse(xml)

    root = tree.getroot()

    if validate:
        validate_tree(root, 'SystemStructureParameterMapping.xsd')

    parameter_mapping = ParameterMapping()

    for m in root.findall('ssm:MappingEntry', namespaces=ns):
        mapping_entry = MappingEntry(**m.attrib)
        mapping_entry.transformation = _get_transformation(m)
        parameter_mapping.mappingEntries.append(mapping_entry)

    return parameter_mapping


def _handle_signal_dictionary(element):

    dictionary = SignalDictionary(**element.attrib)

    for e in element.findall('sss:DictionaryEntry', namespaces=ns):

        entry = DictionaryEntry(name=e.get('name'))

        real = e.find('ssc:Real', namespaces=ns)
        if real is not None:
            entry.type = 'Real'
            entry.unit = real.get('unit')
        else:
            for type in ['Integer', 'Boolean', 'String', 'Enumeration', 'Binary']:
                entry = e.find('ssc:' + type, namespaces=ns)
                if entry is not None:
                    entry.type = type
                    break

        dictionary.entries.append(entry)

    return dictionary


def get_connectors(element):

    connectors = []

    for c in element.findall('ssd:Connectors/ssd:Connector', namespaces=ns):
        connector = Connector(name=c.get('name'), kind=c.get('kind'))
        connectors.append(connector)

    return connectors


def _handle_element(object, element, filename):

    for b in element.findall('ssd:ParameterBindings/ssd:ParameterBinding', namespaces=ns):

        parameter_binding = ParameterBinding(**b.attrib)

        if parameter_binding.source is not None:
            parameter_set = read_ssv(filename, resource=parameter_binding.source)
            parameter_binding.parameterValues.append(parameter_set)

        for s in b.findall('ssd:ParameterValues/ssv:ParameterSet', namespaces=ns):
            parameter_set = _get_parameter_set(s)
            parameter_binding.parameterValues.append(parameter_set)

        for m in b.findall('ssd:ParameterMapping', namespaces=ns):

            source = m.get('source')

            if source is None:
                parameter_mapping = ParameterMapping()
            else:
                parameter_mapping = read_ssm(filename, resource=source)

            parameter_binding.parameterMapping.append(parameter_mapping)

        object.parameterBindings.append(parameter_binding)


def handle_system(system, filename):
    """
    Parameters:
        system      ...
        filename    filename of the SSP file

    Returns:
        A System object
    """

    system_obj = System()

    system_obj.name = system.get('name')
    system_obj.description = system.get('description')
    _handle_element(system_obj, system, filename)

    # for b in system.findall('ssd:ParameterBindings/ssd:ParameterBinding', namespaces=ns):
    #     system_obj.parameterBindings.append(
    #         ParameterBinding(prefix=b.get('prefix'), source=b.get('source'), type=b.get('type')))

    system_obj.connectors = get_connectors(system)

    # Components
    for c in system.findall('ssd:Elements/ssd:Component', namespaces=ns):
        component = Component(name=c.get('name'), source=c.get('source'), type=c.get('type'))
        _handle_element(component, c, filename)
        component.connectors = get_connectors(c)
        system_obj.elements.append(component)

    # SignalDictionaryReferences
    for r in system.findall('ssd:Elements/ssd:SignalDictionaryReference', namespaces=ns):
        reference = SignalDictionaryReference(name=r.get('name'), dictionary=r.get('dictionary'))
        reference.connectors = get_connectors(r)
        system_obj.elements.append(reference)

    # Connections
    for c in system.findall('ssd:Connections/ssd:Connection', namespaces=ns):
        connection = Connection(startElement=c.get('startElement'),
                                startConnector=c.get('startConnector'),
                                endElement=c.get('endElement'),
                                endConnector=c.get('endConnector'))
        # LinearTransformation
        t = c.find('ssd:LinearTransformation', namespaces=ns)
        if t is not None:
            connection.linearTransformation = LinearTransformation(factor=float(t.get('factor', 1.0)),
                                                                   offset=float(t.get('offset', 0.0)))

        system_obj.connections.append(connection)

    # SignalDictionaries
    for d in system.findall('ssd:SignalDictionaries/ssd:SignalDictionary', namespaces=ns):

        source = d.get('source')

        if source is not None:
            # referenced
            with zipfile.ZipFile(filename, 'r') as zf:
                xml = zf.open(source)
                tree = etree.parse(xml)
                sd = tree.getroot()
        else:
            # inline
            sd = d.find('sss:SignalDictionary', namespaces=ns)

        signal_dictionary = _handle_signal_dictionary(sd)

        signal_dictionary.name = d.get('name')
        signal_dictionary.source = d.get('source')
        signal_dictionary.type = d.get('type')

        system_obj.signalDictionaries.append(signal_dictionary)

    # Systems
    for system in system.findall('ssd:Elements/ssd:System', namespaces=ns):
        child_system_obj = handle_system(system, filename=filename)
        system_obj.elements.append(child_system_obj)

    return system_obj


def read_ssd(filename, validate=True):

    with zipfile.ZipFile(filename, 'r') as zf:
        xml = zf.open('SystemStructure.ssd')
        tree = etree.parse(xml)

    root = tree.getroot()

    if validate:
        validate_tree(root, 'SystemStructureDescription.xsd')

    ssd = SystemStructureDescription()

    ssd.version = root.get('version')
    ssd.name = root.get('name')

    # Units
    for u in root.findall('ssd:Units/ssc:Unit', namespaces=ns):
        attr = dict(u.attrib)
        bu = u.find('ssc:BaseUnit', namespaces=ns)
        attr.update(bu.attrib)
        ssd.units.append(Unit(**attr))
    ssd.system = System()

    system = root.find('ssd:System', namespaces=ns)

    ssd.system = handle_system(system, filename=filename)

    # add parent elements
    add_tree_info(ssd.system)
    ssd.system.parent = None

    return ssd


def add_tree_info(element):

    if isinstance(element, System):
        for child in element.elements:
            child.parent = element
            add_tree_info(child)

    for connector in element.connectors:
        connector.parent = element


def build_path(object):

    path = object.name

    while object.parent is not None:
        object = object.parent
        path = object.name + '.' + path

    return path


def find_connectors(element):
    """ Return a list of all connectors in element including (sub-systems)"""

    connectors = []
    connectors += element.connectors

    if isinstance(element, System):
        for child in element.elements:
            connectors += find_connectors(child)

    return connectors


def find_components(system):
    """ Return a list of all components in system including (sub-systems)"""

    components = []

    for element in system.elements:
        if isinstance(element, Component):
            components.append(element)
        elif isinstance(element, System):
            components += find_components(element)

    return components


def get_connections(system, connectors=None):
    """ Create a list of (start_connector, end_connector) from all connections in the system """

    if connectors is None:
        connectors = {}  # path -> object
        for connector in find_connectors(system):
            connectors[build_path(connector)] = connector

    cons = []

    # connections to the outside
    for connector in system.connectors:

        if connector.kind == 'output':

            # find the connection
            for connection in system.connections:
                if connection.endElement is None and connection.endConnector == connector.name:
                    start_p = build_path(system) + '.' + connection.startElement + '.' + connection.startConnector
                    end_p = build_path(connector)
                    break
                elif connection.startElement is None and connection.startConnector == connector.name:
                    start_p = build_path(connector)
                    end_p = build_path(system) + '.' + connection.startElement + '.' + connection.startConnector
                    break

            cons.append((connectors[start_p], connectors[end_p]))

    # internal connections
    for element in system.elements:

        for connector in element.connectors:

            if connector.kind == 'input':
                end_p = build_path(element) + '.' + connector.name

                # find the connection
                for connection in system.connections:
                    if connection.endElement == element.name and connection.endConnector == connector.name:
                        start_p = build_path(system)
                        if connection.startElement is not None:
                            start_p += '.' + connection.startElement
                        start_p += '.' + connection.startConnector
                        break
                    elif connection.startElement == element.name and connection.startConnector == connector.name:
                        start_p = build_path(system)
                        if connection.endElement is not None:
                            start_p += '.' + connection.endElement
                        start_p += '.' + connection.endConnector
                        break

                cons.append((connectors[start_p], connectors[end_p]))

    # continue with the child systems
    for element in system.elements:
        if isinstance(element, System):
            cons += get_connections(element, connectors=connectors)

    return cons
