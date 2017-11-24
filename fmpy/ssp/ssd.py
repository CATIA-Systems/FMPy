from lxml import etree
import zipfile
import os

# namespaces for XML parsing
ns = {
    'ssd': 'http://www.pmsf.net/xsd/SystemStructureDescriptionDraft',
    'ssc': 'http://www.pmsf.net/xsd/SystemStructureCommonDraft',
}


class SystemStructureDescription(object):

    def __init__(self):
        self.version = None
        self.name = None
        self.system = None
        self.units = []


class System(object):

    def __init__(self):
        self.name = None
        self.description = None
        self.connectors = []
        self.elements = []
        self.connections = []
        self.signalDictionaries = []
        self.parameterBindings = []

    def __repr__(self):
        return "System (name: %s, description: %s)" % (self.name, self.description)


class Connector(object):

    def __init__(self, name=None, kind=None):
        self.name = name
        self.kind = kind

    def __repr__(self):
        return "Connector (name: %s, kind: %s)" % (self.name, self.kind)


class Component(object):

    def __init__(self, name=None, source=None, type=None):
        self.name = name
        self.source = source
        self.type = type
        self.connectors = []

    def __repr__(self):
        return "Component (name: %s, source: %s, type: %s)" % (self.name, self.source, self.type)


class SignalDictionaryReference(object):

    def __init__(self, name=None, dictionary=None):
        self.name = name
        self.dictionary = dictionary
        self.connectors = []

    def __repr__(self):
        return "SignalDictionaryReference (name: %s, dictionary: %s)" % (self.name, self.dictionary)


class Connection(object):

    def __init__(self, startElement=None, startConnector=None, endElement=None, endConnector=None):
        self.startElement = startElement
        self.startConnector = startConnector
        self.endElement = endElement
        self.endConnector = endConnector

    def __repr__(self):
        return "Connection (startElement: %s, startConnector: %s, endElement: %s, endConnector: %s)" % (self.startElement, self.startConnector, self.endElement, self.endConnector)


class LinearTransformation(object):

    def __init__(self, factor=1.0, offset=0.0):
        self.factor = factor
        self.offset = offset

    def __repr__(self):
        return "LinearTransformation (factor: %g, offset: %g)" % (self.factor, self.offset)


class ParameterBinding(object):

    def __init__(self, prefix=None, source=None, type=None):
        self.prefix = prefix
        self.source = source
        self.type = type

    def __repr__(self):
        return "ParameterBinding (prefix: %s, source: %s, type: %s)" % (self.prefix, self.source, self.type)


class SignalDictionary(object):

    def __init__(self, name=None):
        self.name = name
        self.entries = []

    def __repr__(self):
        return "SignalDictionary (name: %s)" % self.name


class DictionaryEntry(object):

    def __init__(self, name=None):
        self.name = name
        self.type = None
        self.unit = None

    def __repr__(self):
        return "DictionaryEntry (name: %s, type: %s, unit=%s)" % (self.name, self.type, self.unit)


class Unit(object):

    def __init__(self, name=None):
        self.name = name
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
        return "Unit (name: %s, kg: %d, m: %d, s: %d, A: %d, K: %d, mol: %d, cd: %d, rad: %d, factor: %g, offset: %g)" % (self.name, self.kg, self.m, self.s, self.A, self.K, self.mol, self.cd, self.rad, self.factor, self.offset)


def validate_tree(root, schema_file):

    module_dir, _ = os.path.split(__file__)

    schema = etree.XMLSchema(file=os.path.join(module_dir, 'schema', schema_file))

    if not schema.validate(root):
        message = "Failed to validate SystemStructure.ssd:"
        for entry in schema.error_log:
            message += "\n%s (line %d, column %d): %s" % (entry.level_name, entry.line, entry.column, entry.message)
        raise Exception(message)


def read_ssv(filename, validate=True):

    ns = {
        'ssv': 'http://www.pmsf.net/xsd/SystemStructureParameterValuesDraft',
    }

    tree = etree.parse(filename)

    root = tree.getroot()

    if validate:
        validate_tree(root, 'SystemStructureParameterValues.xsd')

    parameters = {}

    for parameter in root.findall('ssv:Parameters/ssv:Parameter', namespaces=ns):
        name = parameter.get('name')
        real = parameter.find('ssv:Real', namespaces=ns)
        value = real.get('value')
        parameters[name] = float(value)
    return parameters


def get_connectors(element):

    connectors = []

    for c in element.findall('ssd:Connectors/ssd:Connector', namespaces=ns):
        connector = Connector(name=c.get('name'), kind=c.get('kind'))
        connectors.append(connector)

    return connectors


def handle_system(system):

    system_obj = System()

    system_obj.name = system.get('name')
    system_obj.description = system.get('description')

    for b in system.findall('ssd:ParameterBindings/ssd:ParameterBinding', namespaces=ns):
        system_obj.parameterBindings.append(
            ParameterBinding(prefix=b.get('prefix'), source=b.get('source'), type=b.get('type')))

    system_obj.connectors = get_connectors(system)

    # Components
    for c in system.findall('ssd:Elements/ssd:Component', namespaces=ns):
        component = Component(name=c.get('name'), source=c.get('source'), type=c.get('type'))
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
        dictionary = SignalDictionary(name=d.get('name'))
        for e in d.findall('ssd:DictionaryEntry', namespaces=ns):
            entry = DictionaryEntry(name=e.get('name'))
            dictionary.entries.append(entry)
            r = e.find('ssc:Real', namespaces=ns)
            if r is not None:
                entry.unit = r.get('unit')

        system_obj.signalDictionaries.append(dictionary)

    # Systems
    for system in system.findall('ssd:Elements/ssd:System', namespaces=ns):
        child_system_obj = handle_system(system)
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
        unit = Unit(name=u.get('name'))
        b = u.find('ssc:BaseUnit', namespaces=ns)
        for s in ['kg', 'm', 's', 'A', 'K', 'mol', 'cd', 'rad', 'factor', 'offset']:
            value = b.get(s)
            if value is not None:
                setattr(unit, s, float(value) if s in ['factor', 'offset'] else int(value))
        ssd.units.append(unit)

    ssd.system = System()

    system = root.find('ssd:System', namespaces=ns)

    ssd.system = handle_system(system)

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
