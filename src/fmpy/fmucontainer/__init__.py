from os import PathLike
from tempfile import mkdtemp
from typing import List, Tuple, Sequence

from attr import attrs, attrib, Factory

from .. import supported_platforms
from ..model_description import Unit, SimpleType


@attrs(eq=False, auto_attribs=True)
class Variable(object):

    type: str = None
    variability: str = None
    causality: str = None
    initial: str = None
    name: str = None
    start: str = None
    description: str = None
    mapping: Sequence[Tuple[str, str]] = None
    declaredType: str = None
    unit: str = None
    displayUnit: str = None


@attrs(eq=False, auto_attribs=True)
class Component(object):

    filename: PathLike
    name: str


@attrs(eq=False, auto_attribs=True)
class Connection(object):

    startElement: str
    startConnector: str
    endElement: str
    endConnector: str


@attrs(eq=False, auto_attribs=True)
class DefaultExperiment(object):

    startTime: str = None
    stopTime: str = None
    tolerance: str = None
    stepSize: str = None


@attrs(eq=False)
class Configuration(object):

    fmiVersion = attrib(type=str, default=None, repr=False)
    description = attrib(type=str, default=None, repr=False)
    variableNamingConvention = attrib(type=str, default='flat', repr=False)

    defaultExperiment = attrib(type=DefaultExperiment, default=None, repr=False)

    parallelDoStep = attrib(type=bool, default=False, repr=False)

    unitDefinitions = attrib(type=List[Unit], default=Factory(list), repr=False)
    typeDefinitions = attrib(type=List[SimpleType], default=Factory(list), repr=False)

    variables = attrib(type=List[Variable], default=Factory(list), repr=False)
    components = attrib(type=List[Component], default=Factory(list), repr=False)
    connections = attrib(type=List[Connection], default=Factory(list), repr=False)


FMI_TYPES = {

    # FMI 3.0 variable types
    'Float32': 0,
    'DiscreteFloat32': 1,
    'Float64': 2,
    'DiscreteFloat64': 3,
    'Int8': 4,
    'UInt8': 5,
    'Int16': 6,
    'UInt16': 7,
    'Int32': 8,
    'UInt32': 9,
    'Int64': 10,
    'UInt64': 11,
    'Boolean': 12,
    'String': 13,
    'Binary': 14,
    'Clock': 15,

    'Enumeration': 8,

    # Aliases for FMI 1.0 and 2.0
    'Real': 2,
    'DiscreteReal': 3,
    'Integer': 8
}


def create_fmu_container(configuration, output_filename):
    """ Create an FMU from nested FMUs (experimental)

        see tests/test_fmu_container.py for an example
    """

    def xml_encode(s):
        """ Escape non-ASCII characters """

        if s is None:
            return s

        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('"', '&quot;')

        for c in s:
            if ord(c) > 127:
                s = s.replace(c, '&#x' + format(ord(c), 'x') + ';')

        return s

    import jinja2
    import os
    import shutil
    import fmpy
    from fmpy import read_model_description, extract
    import msgpack
    from datetime import datetime, timezone
    from pathlib import Path

    if configuration.fmiVersion not in ['2.0', '3.0']:
        raise Exception(f"fmiVersion must be '2.0' or '3.0' but was { configuration.fmiVersion }.")

    output_filename = Path(output_filename)
    base_filename, _ = os.path.splitext(output_filename)
    model_name = os.path.basename(base_filename)

    unzipdir = Path(mkdtemp())

    basedir = Path(__file__).parent

    shutil.copytree(basedir / 'documentation', unzipdir / 'documentation')

    os.mkdir(unzipdir / 'resources')
    os.mkdir(unzipdir / 'sources')

    sources = [
        'FMI.c',
        'FMI.h',
        'FMI2.c',
        'FMI2.h',
        'FMUContainer.c',
        'FMUContainer.h',
        'mpack.h',
        'mpack-common.c',
        'mpack-common.h',
        'mpack-expect.c',
        'mpack-expect.h',
        'mpack-node.c',
        'mpack-node.h',
        'mpack-platform.c',
        'mpack-platform.h',
        'mpack-reader.c',
        'mpack-reader.h',
        'mpack-writer.c',
        'mpack-writer.h',
    ]

    if configuration.fmiVersion == '2.0':
        sources.append('fmi2Functions.c')
    else:
        sources.append('fmi3Functions.c')
        sources.append('buildDescription.xml')

    for file in sources:
        shutil.copyfile(basedir / 'sources' / file, unzipdir / 'sources' / file)

    data = {
        'parallelDoStep': configuration.parallelDoStep,
        'components': [],
        'variables': [],
        'connections': []
    }

    component_map = {}

    platforms = []

    for i, component in enumerate(configuration.components):
        model_description = read_model_description(component.filename)
        model_identifier = model_description.coSimulation.modelIdentifier
        extract(component.filename, unzipdir / 'resources' / model_identifier)
        variables = dict((v.name, v) for v in model_description.modelVariables)
        component_map[component.name] = (i, variables)

        c = {
            'name': component.name,
            'guid': model_description.guid,
            'modelIdentifier': model_identifier,
        }

        data['components'].append(c)

        platforms.append(set(supported_platforms(component.filename)))

    platforms = platforms[0].intersection(*platforms[1:])  # platforms supported by all components

    platform_map = {
        'darwin64': 'x86_64-darwin',
        'linux64': 'x86_64-linux',
        'win32': 'x86-windows',
        'win64': 'x86_64-windows',
    }

    for platform in platforms:
        src = basedir / 'binaries' / platform
        if src.exists():
            if configuration.fmiVersion == '2.0':
                dst = unzipdir / 'binaries' / platform
            else:
                dst = unzipdir / 'binaries' / platform_map[platform]
            shutil.copytree(src, dst)

    variables_map = {}

    for i, v in enumerate(configuration.variables):
        variables_map[v.name] = (i, v)

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
            'type': FMI_TYPES[v.type],
            'components': component_indices,
            'valueReferences': value_references,
        }

        if v.start is not None:
            if v.type in ['Float64', 'Real']:
                variable['start'] = float(v.start)
            elif v.type in ['Int32', 'Integer', 'Enumeration']:
                variable['start'] = int(v.start)
            elif v.type == 'Boolean':
                if isinstance(v.start, str):
                    if v.start.lower() not in ['false', 'true', '0', '1']:
                        raise Exception(f'The start value "{v.start}" for variable "{v.name}"'
                                        ' could not be converted to Boolean.')
                    else:
                        variable['start'] = v.start.lower() in ['1', 'true']
                else:
                    variable['start'] = bool(v.start)
            elif v.type == 'String':
                variable['start'] = v.start

        data['variables'].append(variable)

    for c in configuration.connections:
        data['connections'].append({
            'type': FMI_TYPES[component_map[c.startElement][1][c.startConnector].type],
            'startComponent': component_map[c.startElement][0],
            'endComponent': component_map[c.endElement][0],
            'startValueReference': component_map[c.startElement][1][c.startConnector].valueReference,
            'endValueReference': component_map[c.endElement][1][c.endConnector].valueReference,
        })

    loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / 'templates')

    environment = jinja2.Environment(loader=loader, trim_blocks=True)

    if configuration.fmiVersion == '2.0':
        template = environment.get_template('FMI2.xml')
    else:
        template = environment.get_template('FMI3.xml')

    def to_literal(value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        else:
            return str(value)

    template.globals.update({
        'xml_encode': xml_encode,
        'to_literal': to_literal,
    })

    xml = template.render(
        system=configuration,
        modelName=model_name,
        description=configuration.description,
        generationDateAndTime=datetime.now(timezone.utc).isoformat(),
        fmpyVersion=fmpy.__version__
    )

    # print(xml)

    with open(unzipdir / 'modelDescription.xml', 'w') as f:
        f.write(xml)

    with open(unzipdir / 'resources' / 'config.mp', 'wb') as f:
        packed = msgpack.packb(data)
        f.write(packed)

    shutil.make_archive(base_filename, 'zip', unzipdir)

    if output_filename.is_file():
        os.remove(output_filename)

    os.rename(base_filename + '.zip', output_filename)

    shutil.rmtree(unzipdir, ignore_errors=True)
