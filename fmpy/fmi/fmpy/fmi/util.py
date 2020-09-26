
def _is_string(s):
    """ Python 2 and 3 compatible type check for strings """

    import sys
    return isinstance(s, basestring if sys.version_info[0] == 2 else str)


def fmu_info(filename, causalities=['input', 'output']):
    """ Dump the info for an FMU """

    from .model_description import read_model_description
    from .fmu import supported_platforms

    md = read_model_description(filename, validate=False)
    platforms = supported_platforms(filename)

    fmi_types = []
    if md.modelExchange is not None:
        fmi_types.append('Model Exchange')
    if md.coSimulation is not None:
        fmi_types.append('Co-Simulation')

    l = []

    l.append("")
    l.append("Model Info")
    l.append("")
    l.append("  FMI Version       %s" % md.fmiVersion)
    l.append("  FMI Type          %s" % ', '.join(fmi_types))
    l.append("  Model Name        %s" % md.modelName)
    l.append("  Description       %s" % md.description)
    l.append("  Platforms         %s" % ', '.join(platforms))
    l.append("  Continuous States %s" % md.numberOfContinuousStates)
    l.append("  Event Indicators  %s" % md.numberOfEventIndicators)
    l.append("  Variables         %s" % len(md.modelVariables))
    l.append("  Generation Tool   %s" % md.generationTool)
    l.append("  Generation Date   %s" % md.generationDateAndTime)

    if md.defaultExperiment:

        ex = md.defaultExperiment

        l.append("")
        l.append('Default Experiment')
        l.append("")
        if ex.startTime:
            l.append("  Start Time        %g" % ex.startTime)
        if ex.stopTime:
            l.append("  Stop Time         %g" % ex.stopTime)
        if ex.tolerance:
            l.append("  Tolerance         %g" % ex.tolerance)
        if ex.stepSize:
            l.append("  Step Size         %g" % ex.stepSize)

    inputs = []
    outputs = []

    for v in md.modelVariables:
        if v.causality == 'input':
            inputs.append(v.name)
        if v.causality == 'output':
            outputs.append(v.name)

    l.append("")
    l.append("Variables (%s)" % ', '.join(causalities))
    l.append("")
    l.append('Name                Causality              Start Value  Unit     Description')
    for v in md.modelVariables:
        if v.causality not in causalities:
            continue

        start = str(v.start) if v.start is not None else ''

        unit = v.declaredType.unit if v.declaredType else v.unit

        args = ['' if s is None else str(s) for s in [v.name, v.causality, start, unit, v.description]]

        l.append('{:19} {:10} {:>23}  {:8} {}'.format(*args))

    return '\n'.join(l)
