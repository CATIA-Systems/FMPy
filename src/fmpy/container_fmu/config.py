from enum import Enum
from pathlib import Path
from typing import Sequence, Literal
from fmpy.model_description import Unit, SimpleType
from attrs import define, field

NamingConvention = Literal["flat", "structured"]


class FMIMajorVersion(Enum):
    FMIMajorVersion2 = 2
    FMIMajorVersion3 = 3


@define(eq=False)
class Variable:
    type: str = None
    variability: str = None
    causality: str = None
    initial: str = None
    name: str = None
    start: list[str] = None
    description: str = None
    mappings: Sequence[tuple[str, str]] = None
    declaredType: str = None
    unit: str = None
    displayUnit: str = None


@define(eq=False)
class Component:
    fmiMajorVersion: FMIMajorVersion
    name: str
    filename: Path


@define(eq=False)
class Connection:
    startElement: str
    startConnectors: list[str]
    endElement: str
    endConnectors: list[str]
    size: int = None


@define(eq=False)
class DefaultExperiment:
    startTime: str = None
    stopTime: str = None
    tolerance: str = None
    stepSize: str = None


@define(eq=False)
class Configuration:
    parallelDoStep: bool = False
    instantiationToken: str = None
    fixedStepSize: float = None
    description: str = None
    variableNamingConvention: NamingConvention = "flat"
    defaultExperiment: DefaultExperiment | None = None
    unitDefinitions: list[Unit] = field(factory=list)
    typeDefinitions: list[SimpleType] = field(factory=list)
    variables: list[Variable] = field(factory=list)
    components: list[Component] = field(factory=list)
    connections: list[Connection] = field(factory=list)
