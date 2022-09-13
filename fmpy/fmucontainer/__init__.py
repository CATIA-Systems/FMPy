from os import PathLike
from tempfile import mkdtemp
from typing import List, Optional, Tuple

from attr import attrs, attrib, Factory

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
    mapping: Tuple[str, str] = None
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


@attrs(eq=False)
class Configuration(object):

    parallelDoStep = attrib(type=bool, default=False, repr=False)

    description = attrib(type=str, default=None, repr=False)
    variableNamingConvention = attrib(type=str, default='flat', repr=False)

    unitDefinitions = attrib(type=List[Unit], default=Factory(list), repr=False)
    typeDefinitions = attrib(type=List[SimpleType], default=Factory(list), repr=False)

    variables = attrib(type=List[Variable], default=Factory(list), repr=False)
    components = attrib(type=List[Component], default=Factory(list), repr=False)
    connections = attrib(type=List[Connection], default=Factory(list), repr=False)


FMI_TYPES = {
    'Real': 2,
    'Integer': 8,
    'Boolean': 12,
    'String': 13,
}


def create_fmu_container(configuration: Configuration,
                         output_filename: str,
                         generation_datetime: Optional[str] = None,
                         validate_model_descriptions: bool=True):
    """ Create an FMU from nested FMUs (experimental)

        see tests/test_fmu_container.py for an example

        Parameters:
            configuration                  configuration of contained FMUs, connections, inputs/outputs, ...
            output_filename                name of the resulting FMU
            generation_datetime            Datetime string added to the resulting model description as "generationDateAndTime" attribute
            validate_model_descriptions    whether to validate the model descriptions that are being read
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

    import os
    import shutil
    import fmpy
    from fmpy import read_model_description, extract
    import msgpack
    from datetime import datetime
    import pytz
    from pathlib import Path

    base_filename, _ = os.path.splitext(output_filename)
    model_name = os.path.basename(base_filename)
    generation_datetime = datetime.now(pytz.utc).isoformat() if generation_datetime is None else generation_datetime

    unzipdir = mkdtemp()

    basedir = os.path.dirname(__file__)

    for directory in ['binaries', 'documentation']:
        shutil.copytree(os.path.join(basedir, directory), os.path.join(unzipdir, directory))

    os.mkdir(os.path.join(unzipdir, 'resources'))

    data = {
        'parallelDoStep': configuration.parallelDoStep,
        'components': [],
        'variables': [],
        'connections': []
    }

    component_map = {}

    for i, component in enumerate(configuration.components):
        model_description = read_model_description(component.filename, validate=validate_model_descriptions)
        model_identifier = model_description.coSimulation.modelIdentifier
        extract(component.filename, os.path.join(unzipdir, 'resources', model_identifier))
        variables = dict((v.name, v) for v in model_description.modelVariables)
        component_map[component.name] = (i, variables)

        c = {
            'name': component.name,
            'guid': model_description.guid,
            'modelIdentifier': model_identifier,
        }

        data['components'].append(c)

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
            if v.type == 'Real':
                variable['start'] = float(v.start)
            elif v.type in ['Enumeration', 'Integer']:
                variable['start'] = int(v.start)
            elif v.type == 'Boolean':
                if isinstance(v.start, str):
                    if v.start.lower() not in ['true', 'false']:
                        raise Exception(f'The start value "{v.start}" for variable "{v.name}"'
                                        ' could not be converted to Boolean.')
                    else:
                        variable['start'] = v.start.lower() == 'true'
                else:
                    variable['start'] = bool(v.start)
            elif v.type == 'String':
                variable['start'] = v.start

        data['variables'].append(variable)

    for c in configuration.connections:
        data['connections'].append({
            'type': component_map[c.startElement][1][c.startConnector].type,
            'startComponent': component_map[c.startElement][0],
            'endComponent': component_map[c.endElement][0],
            'startValueReference': component_map[c.startElement][1][c.startConnector].valueReference,
            'endValueReference': component_map[c.endElement][1][c.endConnector].valueReference,
        })

    write_model_description(unzipdir, configuration, model_name, generation_datetime)
    _write_msgpack_config(unzipdir, data)

    shutil.make_archive(base_filename, 'zip', unzipdir)

    if os.path.isfile(output_filename):
        os.remove(output_filename)

    os.rename(base_filename + '.zip', output_filename)

    shutil.rmtree(unzipdir, ignore_errors=True)

def write_model_description(target_folder: str,
                            configuration: Configuration,
                            model_name: str,
                            generation_datetime: str):
    """ Write model description file according to the configuration (experimental)

        Parameters:
            target_folder              folder to write the model description file into
            configuration              configuration of contained FMUs, connections, inputs/outputs, ...
            model_name                 the model's name
            generation_datetime        Datetime string added to the resulting model description as "generationDateAndTime" attribute
    """
    from pathlib import Path
    import jinja2
    import os

    loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / 'templates')

    environment = jinja2.Environment(loader=loader, trim_blocks=True)

    template = environment.get_template('FMI2.xml')

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
        generationDateAndTime=generation_datetime,
        fmpyVersion=fmpy.__version__
    )

    with open(os.path.join(target_folder, 'modelDescription.xml'), 'w') as f:
        f.write(xml)

def _write_msgpack_config(unzipdir, data):
    with open(os.path.join(unzipdir, 'resources', 'config.mp'), 'wb') as f:
        packed = msgpack.packb(data)
        f.write(packed)
