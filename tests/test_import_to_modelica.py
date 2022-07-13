from fmpy.modelica import import_fmu_to_modelica


def test_import_fmu_to_modelica(dymola, root_dir, resources_dir):

    for model in ['BouncingBall', 'Integrator', 'Types']:
        import_fmu_to_modelica(
            fmu_path=resources_dir / f'{model}.fmu',
            interface_type='Model Exchange',
            package_dir=resources_dir / 'FMITest'
        )

    dymola.loadClass(root_dir / 'fmpy' / 'modelica' / 'FMI' / 'package.mo')

    dymola.loadClass(resources_dir / 'FMITest' / 'package.mo')

    for model in ['BouncingBall', 'Integrator', 'Types']:
        dymola.simulate(f'FMITest.{model}Test')
