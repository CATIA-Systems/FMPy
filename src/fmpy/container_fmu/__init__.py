import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import jinja2
from fmpy import read_model_description
from fmpy.model_description import ModelVariable

from container_fmu.config import Configuration

__version__ = "0.1.0"


def write_model_description(configuration: Configuration, filename: Path):
    template_dir = Path(__file__).parent / "template"

    loader = jinja2.FileSystemLoader(searchpath=template_dir)
    environment = jinja2.Environment(loader=loader, trim_blocks=True)
    template = environment.get_template("FMI3.xml")

    def xml_encode(s):
        """Escape non-ASCII characters"""

        if s is None:
            return s

        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace('"', "&quot;")

        for c in s:
            if ord(c) > 127:
                s = s.replace(c, "&#x" + format(ord(c), "x") + ";")

        return s

    def to_literal(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    template.globals.update(
        {
            "xml_encode": xml_encode,
            "to_literal": to_literal,
        }
    )

    xml = template.render(
        container_fmu_version=__version__,
        generationDateAndTime=datetime.now(timezone.utc).isoformat(),
        system=configuration,
    )

    with open(filename, "w") as f:
        f.write(xml)


def write_configuration(configuration: Configuration, filename: Path):
    data = {
        "containerVersion": __version__,
        "instantiationToken": configuration.instantiationToken,
        "fixedStepSize": configuration.fixedStepSize,
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
            "fmiMajorVersion": str(component.fmiMajorVersion.value),
            "name": component.name,
            "instantiationToken": model_description.instantiationToken,
            "modelIdentifier": model_identifier,
            "path": component.filename.stem,
        }

        data["components"].append(c)

    variables_map = {}

    for i, v in enumerate(configuration.variables):
        variables_map[v.name] = (i, v)

    for i, v in enumerate(configuration.variables):
        mappings = []

        for component_name, variable_name in v.mappings:
            component_index, component_variables = component_map[component_name]
            value_reference = component_variables[variable_name].valueReference
            mappings.append((component_index, value_reference))

        variable = {
            "variableType": v.type,
            "mappings": mappings,
        }

        if v.start is not None:
            variable["start"] = v.start

        data["variables"].append(variable)

    for c in configuration.connections:
        src_value_references = [
            component_map[c.startElement][1][variable_name].valueReference
            for variable_name in c.startConnectors
        ]
        dst_value_references = [
            component_map[c.endElement][1][variable_name].valueReference
            for variable_name in c.endConnectors
        ]

        size = 0
        for variable_name in c.startConnectors:
            variable = component_map[c.startElement][1][variable_name]
            size += np.prod(variable.shape) if variable.shape else 1

        data["connections"].append(
            {
                "variableType": component_map[c.startElement][1][
                    c.startConnectors[0]
                ].type,
                "srcComponent": component_map[c.startElement][0],
                "dstComponent": component_map[c.endElement][0],
                "srcValueReferences": src_value_references,
                "dstValueReferences": dst_value_references,
                "size": size,
            }
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
