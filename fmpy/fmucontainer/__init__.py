from tempfile import mkdtemp

from attr import attrs


@attrs(eq=False, auto_attribs=True)
class Variable(object):

    type: str = None
    variability: str = None
    causality: str = None
    name: str = None
    start: str = None
    description: str = None
    mapping: str = None


@attrs(eq=False, auto_attribs=True)
class Connection(object):

    startElement: str
    startConnector: str
    endElement: str
    endConnector: str


def create_fmu_container(configuration, output_filename):
    """ Create an FMU from nested FMUs (experimental)

        see tests/test_fmu_container.py for an example
    """

    def xml_encode(s):
        """ Escape non-ASCII characters """

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

    for i, component in enumerate(configuration['components']):
        model_description = read_model_description(component['filename'])
        model_identifier = model_description.coSimulation.modelIdentifier
        extract(component['filename'], os.path.join(unzipdir, 'resources', model_identifier))
        variables = dict((v.name, v) for v in model_description.modelVariables)
        component_map[component['name']] = (i, variables)
        data['components'].append({
            'name': component['name'],
            'guid': model_description.guid,
            'modelIdentifier': model_identifier,
        })

    variables_map = {}

    for i, v in enumerate(configuration['variables']):
        variables_map[v.name] = (i, v)

    mv = ''  # model variables
    mo = ''  # model outputs

    for i, v in enumerate(configuration['variables']):

        component_indices = []
        value_references = []

        # config.mp
        for component_name, variable_name in v.mapping:
            component_index, component_variables = component_map[component_name]
            value_reference = component_variables[variable_name].valueReference
            component_indices.append(component_index)
            value_references.append(value_reference)

        data['variables'].append({
            'components': component_indices,
            'valueReferences': value_references
        })

        # modelDescription.xml
        start = f' start="{ v.start }"' if v.start else ''
        mv += f'\n    <ScalarVariable name="{ v.name }" valueReference="{ i }" variability="{ v.variability }" causality="{ v.causality }" description="{ v.description }">'
        mv += f'\n      <{v.type}{ start }/>'
        mv += f'\n    </ScalarVariable>'

        if v.causality == 'output':
            mo += f'\n      <Unknown index="{ i + 1 }"/>'

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<fmiModelDescription
  fmiVersion="2.0"
  modelName="{ model_name }"
  guid=""
  description="{ configuration.get('description', '') }"
  generationTool="FMPy {fmpy.__version__} FMU Container"
  generationDateAndTime="{ datetime.now(pytz.utc).isoformat() }">

  <CoSimulation modelIdentifier="FMUContainer">
    <SourceFiles>
      <File name="FMUContainer.c"/>
      <File name="mpack.c"/>
    </SourceFiles>
  </CoSimulation>

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

    for c in configuration['connections']:
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
