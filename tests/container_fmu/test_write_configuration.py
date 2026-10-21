import json
from pathlib import Path
from fmpy import read_model_description
from fmpy.container_fmu import write_configuration
from fmpy.container_fmu.config import Component, Configuration, Connection
from fmpy.model_description import ModelDescription, ModelVariable, CoSimulation, DefaultExperiment, Unknown


def test_write_configuration_fmi2_connection_types(work_dir, reference_fmus_dist_dir):
    vdp_path = reference_fmus_dist_dir / "2.0" / "VanDerPol.fmu"
    ft_path = reference_fmus_dist_dir / "2.0" / "Feedthrough.fmu"

    vdp_md = read_model_description(vdp_path)
    ft_md = read_model_description(ft_path)

    v = {x.name: x for x in vdp_md.modelVariables}
    f = {x.name: x for x in ft_md.modelVariables}

    vdp = Component(name="vdp", filename=vdp_path, modelDescription=vdp_md)
    ft = Component(name="ft", filename=ft_path, modelDescription=ft_md)

    out_var = ModelVariable(
        type="Real", variability="continuous", causality="output", initial="calculated", name="y"
    )
    md = ModelDescription(
        fmiVersion="2.0",
        modelName="Container",
        instantiationToken="{00000000-0000-0000-0000-000000000001}",
        defaultExperiment=DefaultExperiment(stopTime="1", stepSize="0.01"),
        coSimulation=CoSimulation(fixedInternalStepSize=0.01),
        modelVariables=[
            ModelVariable(type="Real", variability="continuous", causality="independent", name="time"),
            out_var,
        ],
    )
    md.outputs = [Unknown(variable=out_var)]
    md.initialUnknowns = [Unknown(variable=out_var)]

    cfg = Configuration(
        parallelDoStep=False,
        modelDescription=md,
        components=[vdp, ft],
        connections=[
            Connection(vdp, [v["x0"]], ft, [f["Float64_continuous_input"]]),
            Connection(ft, [f["Boolean_output"]], ft, [f["Boolean_input"]]),
            Connection(ft, [f["Int32_output"]], ft, [f["Int32_input"]]),
            Connection(ft, [f["Enumeration_output"]], ft, [f["Enumeration_input"]]),
            Connection(ft, [f["String_output"]], ft, [f["String_input"]]),
        ],
        variableMappings={out_var: [(vdp, v["x0"])]},
    )

    out_file = work_dir / "container_test_fmi2.json"
    write_configuration(cfg, out_file)

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Connections must have translated FMI 3.0 types accepted by the runner
    assert data["connections"][0]["variableType"] == "Float64"
    assert data["connections"][1]["variableType"] == "Boolean"
    assert data["connections"][2]["variableType"] == "Int32"
    assert data["connections"][3]["variableType"] == "Int32"
    assert data["connections"][4]["variableType"] == "String"

    # Variables must also have translated FMI 3.0 types
    assert data["variables"][0]["variableType"] == "Float64"
