from pathlib import Path
from shutil import move

import pytest

from fmpy.modelica import import_fmu_to_modelica


def pymola_available():
    try:
        import pymola
        return True
    except:
        return False


@pytest.mark.skipif(not pymola_available(), reason="Pymola was not found")
def test_import_fmu_to_modelica(dymola, root_dir, resources_dir):

    dymola.loadClass(root_dir / 'fmpy' / 'modelica' / 'FMI' / 'package.mo')

    dymola.loadClass(resources_dir / 'FMITest' / 'package.mo')

    for model in ['BouncingBall', 'Feedthrough', 'Integrator', 'Stair', 'ThreeSprings', 'Types']:
        if not (resources_dir / f'{model}.fmu').exists():
            dymola.translateModelFMU(f'FMITest.Models.{model}', modelName=model, fmiVersion='2', fmiType='all')
            fmu_path = Path(dymola.getWorkingDirectory()) / f'{model}.fmu'
            move(fmu_path, resources_dir)

    for interface_type, suffix in [('Co-Simulation', 'CS'), ('Model Exchange', 'ME')]:
        for model in ['BouncingBall', 'Feedthrough', 'Integrator', 'Stair', 'ThreeSprings', 'Types']:
            import_fmu_to_modelica(
                fmu_path=resources_dir / f'{model}.fmu',
                model_path=resources_dir / 'FMITest' / f'{model}_{suffix}.mo',
                interface_type=interface_type,
            )

    dymola.loadClass(resources_dir / 'FMITest' / 'package.mo')

    for suffix in ['CS', 'ME']:
        for model in ['BouncingBall', 'Feedthrough', 'Integrator', 'Stair', 'ThreeSprings', 'Types']:
            dymola.simulate(f'FMITest.{model}_{suffix}')
