from tempfile import mkdtemp


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
    vi = 0  # variable index

    mv = ''
    mo = ''

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
        for name in component['variables']:
            v = variables[name]
            data['variables'].append({'component': i, 'valueReference': v.valueReference})
            name = component['name'] + '.' + v.name
            description = v.description
            if name in configuration['variables']:
                mapping = configuration['variables'][name]
                if 'name' in mapping:
                    name = mapping['name']
                if 'description' in mapping:
                    description = mapping['description']
            description = ' description="%s"' % xml_encode(description) if description else ''

            # model variables
            mv += f'    <ScalarVariable name="{ xml_encode(name) }" valueReference="{ vi }" causality="{ v.causality }" variability="{ v.variability }"{ description }>\n'
            mv += f'      <{v.type}'
            if v.start:
                mv += f' start="{v.start}"'
            mv += f'/>\n'
            mv += f'    </ScalarVariable>\n'

            # model structure
            if v.causality == 'output':
                mo += f'      <Unknown index="{ vi + 1 }"/>\n'

            vi += 1

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

  <ModelVariables>
{ mv }  </ModelVariables>

  <ModelStructure>
'''

    if mo:
        xml += '    <Outputs>\n'
        xml += mo
        xml += '    </Outputs>\n'
        xml += '    <InitialUnknowns>\n'
        xml += mo
        xml += '    </InitialUnknowns>'

    xml += '''
  </ModelStructure>

</fmiModelDescription>
'''

    for sc, sv, ec, ev in configuration['connections']:
        data['connections'].append({
            'type': component_map[sc][1][sv].type,
            'startComponent': component_map[sc][0],
            'endComponent': component_map[ec][0],
            'startValueReference': component_map[sc][1][sv].valueReference,
            'endValueReference': component_map[ec][1][ev].valueReference,
        })

    with open(os.path.join(unzipdir, 'modelDescription.xml'), 'w') as f:
        f.write(xml)

    with open(os.path.join(unzipdir, 'resources', 'config.mp'), 'wb') as f:
        packed = msgpack.packb(data)
        f.write(packed)

    shutil.make_archive(base_filename, 'zip', unzipdir)

    if os.path.isfile(output_filename):
        os.remove(output_filename)

    os.rename(base_filename + '.zip', output_filename)

    shutil.rmtree(unzipdir, ignore_errors=True)
