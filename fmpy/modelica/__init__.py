def generate_examples():

    from .. import extract
    from ..util import download_file
    from pathlib import Path

    url = r'https://github.com/modelica/Reference-FMUs/releases/download/v0.0.25/Reference-FMUs-0.0.25.zip'
    checksum = '62e1a89c7e05b67857e5ebb834502dc06466b04cd14065fd72b2af2e3c9aea8d'
    archive = download_file(url=url, checksum=checksum)

    dist = Path(extract(archive))

    modelica = Path(__file__).parent

    for fmi_version in [2, 3]:
        for interface_type in ['CoSimulation', 'ModelExchange']:
            for model in ['BouncingBall', 'Dahlquist', 'Feedthrough', 'Stair', 'Resource', 'VanDerPol']:
                import_fmu_to_modelica(
                    fmu_path=dist / f'{fmi_version}.0' / f'{model}.fmu',
                    model_path=modelica / 'FMI' / 'Examples' / f'FMI{fmi_version}' / interface_type / f'{model}.mo',
                    interface_type=interface_type,
                )


def import_fmu_to_modelica(fmu_path, model_path, interface_type):

    from os import makedirs
    from pathlib import Path

    import jinja2
    from fmpy import extract, read_model_description
    from fmpy.util import sha256_checksum

    fmu_path = Path(fmu_path)
    model_path = Path(model_path)
    model_name = model_path.stem

    package_dir = Path(model_path).parent

    if not (package_dir / 'package.mo').is_file():
        raise Exception(f"{package_dir} is not a package of a Modelica library.")

    model_description = read_model_description(fmu_path)

    if model_description.defaultExperiment is not None and model_description.defaultExperiment.stepSize is not None:
        communicationStepSize = model_description.defaultExperiment.stepSize
    else:
        communicationStepSize = '1e-2'

    if interface_type == 'ModelExchange':
        model_identifier = model_description.modelExchange.modelIdentifier
        IT = 'ME'
    elif interface_type == 'CoSimulation':
        model_identifier = model_description.coSimulation.modelIdentifier
        IT = 'CS'
    else:
        raise Exception(f"interface_type must be 'ModelExchange' or 'CoSimulation', but was '{interface_type}'.")

    package_root = package_dir

    package = package_root.name

    while (package_root.parent / 'package.order').is_file():
        package_root = package_root.parent
        package = package_root.name + '.' + package

    hash = sha256_checksum(fmu_path)

    hash = hash[:7]

    unzipdir = package_root / 'Resources' / 'FMUs' / hash

    makedirs(unzipdir, exist_ok=True)

    extract(filename=fmu_path, unzipdir=unzipdir)

    loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / 'templates')

    environment = jinja2.Environment(loader=loader, trim_blocks=True, block_start_string='@@',
                                     block_end_string='@@', variable_start_string='@=', variable_end_string='=@')

    fmiMajorVersion = int(model_description.fmiVersion[0])

    template = environment.get_template(f'FMI{fmiMajorVersion}_{IT}.mo')

    parameters = []

    inputs = []
    outputs = []

    for variable in model_description.modelVariables:

        if variable.type not in {'Float64', 'Int32', 'Real', 'Integer', 'Boolean', 'String'}:
            continue

        if variable.causality == 'parameter':
            parameters.append(variable)
        elif variable.causality == 'input':
            inputs.append(variable)
        elif variable.causality == 'output':
            outputs.append(variable)

    width = 1200
    height = max(200, 100 * max(len(inputs), len(outputs)))

    x0 = -int(width / 2)
    x1 = int(width / 2)
    y0 = -int(height / 2)
    y1 = int(height / 2)

    annotations = dict()

    for i, variable in enumerate(inputs):
        y = y1 - (i + 1) * (height / (1 + len(inputs)))
        annotations[variable.name] = f'annotation (Placement(transformation(extent={{ {{ {x0 - 40}, {y - 20} }}, {{ {x0}, {y + 20} }} }}), iconTransformation(extent={{ {{ {x0 - 40}, {y - 20} }}, {{ {x0}, {y + 20} }} }})))'

    for i, variable in enumerate(outputs):
        y = y1 - (i + 1) * (height / (1 + len(outputs)))
        annotations[variable.name] = f'annotation (Placement(transformation(extent={{ {{ {x1}, {y - 10} }}, {{ {x1 + 20}, {y + 10} }} }}), iconTransformation(extent={{ {{ {x1}, {y - 10} }}, {{ {x1 + 20}, {y + 10} }} }})))'

    def as_array(values, default):
        if len(values) > 0:
            return '{ ' + ', '.join(map(str, values)) + ' }'
        else:
            return f'fill({default}, 0)'

    def as_quoted_array(values, default):
        if len(values) > 0:
            return '{ ' + ', '.join(map(lambda v: f"'{v}'", values)) + ' }'
        else:
            return f'fill({default}, 0)'

    def start_value(variable):
        if variable.type == 'Boolean':
            return 'true' if variable.start in ['true', '1'] else 'false'
        elif variable.type == 'String':
            return f'"{variable.start}"'
        else:
            return str(variable.start)

    def modelica_type(variable):
        if variable.declaredType is not None and variable.declaredType.name.startswith('Modelica.'):
            return variable.declaredType.name
        else:
            return variable.type

    template.globals.update({
        'as_array': as_array,
        'as_quoted_array': as_quoted_array,
        'start_value': start_value,
        'modelica_type': modelica_type
    })

    stopTime = getattr(model_description.defaultExperiment, 'stopTime', 1)

    class_text = template.render(
        hash=hash,
        rootPackage=package_root.name,
        package=package,
        description=model_description.description,
        fmiMajorVersion=fmiMajorVersion,
        modelName=model_name,
        modelIdentifier=model_identifier,
        interfaceType=0 if interface_type == 'ModelExchange' else 1,
        instantiationToken=model_description.guid,
        nx=model_description.numberOfContinuousStates,
        nz=model_description.numberOfEventIndicators,
        parameters=parameters,
        communicationStepSize=communicationStepSize,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        inputs=inputs,
        outputs=outputs,
        annotations=annotations,
        realInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Real'],
        realInputs=[v.name for v in inputs if v.type == 'Real'],
        integerInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Integer'],
        integerInputs=[v.name for v in inputs if v.type == 'Integer'],
        booleanInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Boolean'],
        booleanInputs=[v.name for v in inputs if v.type == 'Boolean'],
        stopTime=stopTime
    )

    with open(model_path, 'w') as f:
        f.write(class_text)

    if (package_dir / 'package.order').is_file():
        with open(package_dir / 'package.order', 'r') as f:
            package_order = list(map(lambda l: l.strip(), f.readlines()))
    else:
        package_order = []

    if model_name not in package_order:
        with open(package_dir / 'package.order', 'a') as f:
            f.write(model_name + '\n')
