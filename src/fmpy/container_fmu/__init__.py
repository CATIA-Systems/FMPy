import json
from pathlib import Path
import numpy as np
from fmpy import read_model_description
from fmpy.container_fmu.config import Configuration
from fmpy.model_description import ModelVariable

__version__ = "0.1.0"


def _to_fmi3_type(variable_type: str) -> str:
    """Map FMI 2.0 type names to FMI 3.0 type names accepted by the container runner."""
    if variable_type == "Real":
        return "Float64"
    elif variable_type in ("Integer", "Enumeration"):
        return "Int32"
    return variable_type


def write_configuration(configuration: Configuration, filename: Path):

    data = {
        "containerVersion": __version__,
        "instantiationToken": configuration.modelDescription.instantiationToken,
        "fixedStepSize": configuration.modelDescription.coSimulation.fixedInternalStepSize,
        "parallelDoStep": configuration.parallelDoStep,
        "components": [],
        "variables": [],
        "connections": [],
    }

    component_map: dict[str, tuple[int, dict[str, ModelVariable]]] = {}

    for i, component in enumerate(configuration.components):
        model_description = read_model_description(component.filename)
        model_identifier = model_description.coSimulation.modelIdentifier
        # extract(component.filename, unzipdir / 'resources' / model_identifier)
        variables = dict((v.name, v) for v in model_description.modelVariables)
        component_map[component.name] = (i, variables)

        c = {
            "fmiMajorVersion": str(component.modelDescription.fmiMajorVersion),
            "name": component.name,
            "instantiationToken": model_description.instantiationToken,
            "modelIdentifier": model_identifier,
            "path": component.filename.stem,
        }

        data["components"].append(c)

    variables_map = {}

    for i, v in enumerate(configuration.modelDescription.modelVariables):
        variables_map[v.name] = (i, v)

    for i, (container_variable, m) in enumerate(configuration.variableMappings.items()):

        mappings = []

        for component, component_variable in m:
            mappings.append((
                configuration.components.index(component),
                component_variable.valueReference
            ))

        variable_type = _to_fmi3_type(container_variable.type)

        variable = {
            "variableType": variable_type,
            "mappings": mappings,
        }

        if container_variable.start is not None:
            # TODO: handle arrays
            variable["start"] = [container_variable.start]

        data["variables"].append(variable)

    for c in configuration.connections:

        size = 0

        for variable in c.startConnectors:
            size += np.prod(variable.shape) if variable.shape else 1

        data["connections"].append(
            {
                "variableType": _to_fmi3_type(c.startConnectors[0].type),
                "srcComponent": configuration.components.index(c.startElement),
                "dstComponent": configuration.components.index(c.endElement),
                "srcValueReferences": list(map(lambda v: v.valueReference, c.startConnectors)),
                "dstValueReferences": list(map(lambda v: v.valueReference, c.endConnectors)),
                "size": size,
            }
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
