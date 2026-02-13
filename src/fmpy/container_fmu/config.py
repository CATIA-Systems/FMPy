from attrs import define
from pathlib import Path

from fmpy.model_description import ModelDescription, ModelVariable


@define
class Component:
    name: str
    filename: Path
    modelDescription: ModelDescription


@define
class Connection:
    startElement: Component
    startConnectors: list[ModelVariable]
    endElement: Component
    endConnectors: list[ModelVariable]
    size: int | None = None


@define
class Configuration:
    parallelDoStep: bool
    modelDescription: ModelDescription
    components: list[Component]
    connections: list[Connection]
    variableMappings: dict[ModelVariable, list[tuple[Component, ModelVariable]]]
