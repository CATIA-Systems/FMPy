from tempfile import mkdtemp
from typing import List, Tuple
from attr import attrs, attrib, Factory
from ..model_description import Unit, BaseUnit, DisplayUnit, SimpleType


@attrs(eq=False, auto_attribs=True)
class Variable(object):

    type: str = None
    variability: str = None
    causality: str = None
    name: str = None
    start: str = None
    description: str = None
    mapping: Tuple[str, str] = None
    declaredType: str = None
    unit: str = None
    displayUnit: str = None


@attrs(eq=False, auto_attribs=True)
class Component(object):

    filename: str
    name: str


@attrs(eq=False, auto_attribs=True)
class Connection(object):

    startElement: str
    startConnector: str
    endElement: str
    endConnector: str


@attrs(eq=False)
class Configuration(object):

    description = attrib(type=str, default=None, repr=False)
    variableNamingConvention = attrib(type=str, default='flat', repr=False)

    unitDefinitions = attrib(type=List[Unit], default=Factory(list), repr=False)
    typeDefinitions = attrib(type=List[SimpleType], default=Factory(list), repr=False)

    variables = attrib(type=List[Variable], default=Factory(list), repr=False)
    components = attrib(type=List[Component], default=Factory(list), repr=False)
    connections = attrib(type=List[Connection], default=Factory(list), repr=False)


def create_fmu_container(configuration, output_filename):
    """ Create an FMU from nested FMUs (experimental)

        see tests/test_fmu_container.py for an example
    """

    def xml_encode(s):
        """ Escape non-ASCII characters """

        if s is None:
            return ""

        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('"', '&quot;')

        for c in s:
            if ord(c) > 127:
                s = s.replace(c, '&#x' + format(ord(c), 'x') + ';')

        return s

    import os
    import shutil
    import fmpy
    from fmpy import read_model_description, extract
    import msgpack
    from datetime import datetime
    import pytz

    base_filename, _ = os.path.splitext(output_filename)
    model_name = os.path.basename(base_filename)

    unzipdir = mkdtemp()

    basedir = os.path.dirname(__file__)

    for directory in ['binaries', 'documentation', 'sources']:
        shutil.copytree(os.path.join(basedir, directory), os.path.join(unzipdir, directory))

    os.mkdir(os.path.join(unzipdir, 'resources'))

    data = {
        'components': [],
        'variables': [],
        'connections': []
    }

    component_map = {}

    for i, component in enumerate(configuration.components):
        model_description = read_model_description(component.filename)
        model_identifier = model_description.coSimulation.modelIdentifier
        extract(component.filename, os.path.join(unzipdir, 'resources', model_identifier))
        variables = dict((v.name, v) for v in model_description.modelVariables)
        component_map[component.name] = (i, variables)
        data['components'].append({
            'name': component.name,
            'guid': model_description.guid,
            'modelIdentifier': model_identifier,
        })

    variables_map = {}

    for i, v in enumerate(configuration.variables):
        variables_map[v.name] = (i, v)

    unit_defintions = ''

    def to_xml(o):

        xml = f'<{type(o).__name__}'

        for a in dir(o):
            if not a.startswith('_'):
                v = getattr(o, a)
                if v:
                    xml += f' {a}="{v}"'

        xml += '/>'

        return xml

    if configuration.unitDefinitions:

        unit_defintions += '\n  <UnitDefinitions>'

        for unit in configuration.unitDefinitions:
            unit_defintions += f'\n    <Unit name="{unit.name}">'
            if unit.baseUnit:
                unit_defintions += '\n      ' + to_xml(unit.baseUnit)
            for displayUnit in unit.displayUnits:
                unit_defintions += '\n      ' + to_xml(displayUnit)
            unit_defintions += '\n    </Unit>'

        unit_defintions += '\n  </UnitDefinitions>'

    type_definitions = ''

    if configuration.typeDefinitions:

        type_definitions += '\n  <TypeDefinitions>'

        for simpleType in configuration.typeDefinitions:
            type_definitions += f'\n    <SimpleType name="{simpleType.name}">'
            type_definitions += f'\n      <{simpleType.type}'
            if simpleType.quantity:
                type_definitions += f' quantity="{simpleType.quantity}'
            if simpleType.unit:
                type_definitions += f' unit="{simpleType.unit}"'
            if simpleType.displayUnit:
                type_definitions += f' displayUnit="{simpleType.displayUnit}"'
            type_definitions += '/>'
            type_definitions += '\n    </SimpleType>'

        type_definitions += '\n  </TypeDefinitions>'

    mv = ''  # model variables
    mo = ''  # model outputs

    for i, v in enumerate(configuration.variables):

        component_indices = []
        value_references = []

        # config.mp
        for component_name, variable_name in v.mapping:
            component_index, component_variables = component_map[component_name]
            value_reference = component_variables[variable_name].valueReference
            component_indices.append(component_index)
            value_references.append(value_reference)

        variable = {
            'components': component_indices,
            'valueReferences': value_references,
        }

        if v.start is not None:
            if v.type == 'Real':
                variable['start'] = float(v.start)
            elif v.type in ['Enumeration', 'Integer']:
                variable['start'] = int(v.start)
            elif v.type == 'Boolean':
                variable['start'] = bool(v.start)
            elif v.type == 'String':
                variable['start'] = v.start

        data['variables'].append(variable)

        # modelDescription.xml
        start = f' start="{ v.start }"' if v.start else ''
        mv += f'\n    <ScalarVariable name="{ xml_encode(v.name) }" valueReference="{ i }" variability="{ v.variability }" causality="{ v.causality }" description="{ xml_encode(v.description) }">'
        mv += f'\n      <{v.type}{ start }'
        if v.declaredType:
            mv += f' declaredType="{v.declaredType}"'
        if v.unit:
            mv += f' unit="{v.unit}"'
        if v.displayUnit:
            mv += f' displayUnit="{v.displayUnit}"'
        mv += '/>'
        mv += f'\n    </ScalarVariable>'

        if v.causality == 'output':
            mo += f'\n      <Unknown index="{ i + 1 }"/>'

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<fmiModelDescription
  fmiVersion="2.0"
  modelName="{ model_name }"
  guid=""
  description="{ xml_encode(configuration.description) }"
  generationTool="FMPy {fmpy.__version__} FMU Container"
  generationDateAndTime="{ datetime.now(pytz.utc).isoformat() }"
  variableNamingConvention="{ configuration.variableNamingConvention }">
  
  <CoSimulation modelIdentifier="FMUContainer">
    <SourceFiles>
      <File name="FMUContainer.c"/>
      <File name="mpack.c"/>
    </SourceFiles>
  </CoSimulation>

  { unit_defintions }

  { type_definitions }

  <ModelVariables>{ mv }
  </ModelVariables>

  <ModelStructure>
    <Outputs>{mo}
    </Outputs>
    <InitialUnknowns>{ mo }
    </InitialUnknowns>
  </ModelStructure>

</fmiModelDescription>
'''

    with open(os.path.join(unzipdir, 'modelDescription.xml'), 'w') as f:
        f.write(xml)

    for c in configuration.connections:
        data['connections'].append({
            'type': component_map[c.startElement][1][c.startConnector].type,
            'startComponent': component_map[c.startElement][0],
            'endComponent': component_map[c.endElement][0],
            'startValueReference': component_map[c.startElement][1][c.startConnector].valueReference,
            'endValueReference': component_map[c.endElement][1][c.endConnector].valueReference,
        })

    with open(os.path.join(unzipdir, 'resources', 'config.mp'), 'wb') as f:
        packed = msgpack.packb(data)
        f.write(packed)

    shutil.make_archive(base_filename, 'zip', unzipdir)

    if os.path.isfile(output_filename):
        os.remove(output_filename)

    os.rename(base_filename + '.zip', output_filename)

    shutil.rmtree(unzipdir, ignore_errors=True)
