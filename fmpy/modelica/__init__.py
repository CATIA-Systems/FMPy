def import_fmu_to_modelica(fmu_path, interface_type, package_dir, model_name=None):

    from os import makedirs
    from pathlib import Path

    import jinja2
    from fmpy import extract, read_model_description

    fmu_path = Path(fmu_path)

    package_dir = Path(package_dir)

    if not (package_dir / 'package.order').is_file():
        raise Exception(f"{package_dir} is not a package of a Modelica library.")

    communicationStepSize = 1e-2

    model_description = read_model_description(fmu_path)

    if interface_type == 'Model Exchange':
        modelIdentifier = model_description.modelExchange.modelIdentifier
    else:
        modelIdentifier = model_description.coSimulation.modelIdentifier

    if not model_name:
        model_name = modelIdentifier

    unzipdir = package_dir / 'Resources' / 'FMUs' / modelIdentifier

    makedirs(unzipdir, exist_ok=True)

    extract(filename=fmu_path, unzipdir=unzipdir)

    package_root = package_dir

    while (package_root.parent / 'package.order').is_file():
        package_root = package_root.parent

    loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / 'templates')

    environment = jinja2.Environment(loader=loader, trim_blocks=True, block_start_string='@@',
                                     block_end_string='@@', variable_start_string='@=', variable_end_string='=@')

    if interface_type == 'Co-Simulation':
        template = environment.get_template(f'FMI2_CS.mo')
    else:
        template = environment.get_template(f'FMI2_ME.mo')

    parameters = []

    inputs = []
    outputs = []

    width = 400
    height = 200

    x0 = -int(width / 2)
    x1 = int(width / 2)
    y0 = -int(height / 2)
    y1 = int(height / 2)

    for variable in model_description.modelVariables:

        if variable.type not in {'Real', 'Integer', 'Boolean'}:
            continue

        if variable.causality == 'parameter':
            parameters.append(variable)
        elif variable.causality == 'input':
            inputs.append(variable)
        elif variable.causality == 'output':
            outputs.append(variable)

    labels = []
    annotations = dict()

    for i, variable in enumerate(inputs):
        y = y1 - (i + 1) * (height / (1 + len(inputs)))
        annotations[
            variable.name] = f'annotation (Placement(transformation(extent={{ {{ {x0 - 40}, {y - 20} }}, {{ {x0}, {y + 20} }} }}), iconTransformation(extent={{ {{ {x0 - 40}, {y - 20} }}, {{ {x0}, {y + 20} }} }})))'
        labels.append(
            f', Text(extent={{ {{ {x0 + 10}, {y - 10} }}, {{ -10, {y + 10} }} }}, textColor={{0,0,0}}, textString="{variable.name}", horizontalAlignment=TextAlignment.Left)')

    for i, variable in enumerate(outputs):
        y = y1 - (i + 1) * (height / (1 + len(outputs)))
        annotations[
            variable.name] = f'annotation (Placement(transformation(extent={{ {{ {x1}, {y - 10} }}, {{ {x1 + 20}, {y + 10} }} }}), iconTransformation(extent={{ {{ {x1}, {y - 10} }}, {{ {x1 + 20}, {y + 10} }} }})))'
        labels.append(
            f', Text(extent={{ {{ 10, {y - 10} }}, {{ {x1 - 10}, {y + 10} }} }}, textColor={{0,0,0}}, textString="{variable.name}", horizontalAlignment=TextAlignment.Right)')

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
        else:
            return str(variable.start)

    template.globals.update({
        'as_array': as_array,
        'as_quoted_array': as_quoted_array,
        'start_value': start_value
    })

    class_text = template.render(
        package=package_root.name,
        modelIdentifier=modelIdentifier,
        instanceName=model_description.modelName,
        interfaceType=0 if interface_type == 'Model Exchange' else 1,
        instantiationToken=model_description.guid,
        nx=model_description.numberOfContinuousStates,
        nz=model_description.numberOfEventIndicators,
        parameters=parameters,
        communicationStepSize=communicationStepSize,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        labels=' '.join(labels),
        inputs=inputs,
        outputs=outputs,
        annotations=annotations,
        realInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Real'],
        realInputs=[v.name for v in inputs if v.type == 'Real'],
        integerInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Integer'],
        integerInputs=[v.name for v in inputs if v.type == 'Integer'],
        booleanInputVRs=[str(v.valueReference) for v in inputs if v.type == 'Boolean'],
        booleanInputs=[v.name for v in inputs if v.type == 'Boolean'],
    )

    with open(package_dir / f'{modelIdentifier}.mo', 'w') as f:
        f.write(class_text)

    with open(package_dir / 'package.order', 'a') as f:
        f.write(modelIdentifier + '\n')
