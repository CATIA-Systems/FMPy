from ctypes import POINTER, c_size_t, cast
from fmpy.fmi3 import _FMU3, fmi3OK


def test_get_variable_dependencies():
    fmu = object.__new__(_FMU3)
    fmu.component = 1

    def fake_get_num_deps(instance, vr, n_deps_ptr):
        assert instance == 1
        assert vr.value == 42
        cast(n_deps_ptr, POINTER(c_size_t))[0] = 2
        return fmi3OK

    def fake_get_deps(
        instance,
        dependent,
        elem_dep,
        independents,
        elem_indep,
        dep_kinds,
        n_deps,
    ):
        assert instance == 1
        assert dependent.value == 42
        assert n_deps == 2
        elem_dep[0], elem_dep[1] = 0, 1
        independents[0], independents[1] = 10, 20
        elem_indep[0], elem_indep[1] = 0, 0
        dep_kinds[0], dep_kinds[1] = 1, 2
        return fmi3OK

    fmu.fmi3GetNumberOfVariableDependencies = fake_get_num_deps
    fmu.fmi3GetVariableDependencies = fake_get_deps

    assert fmu.getNumberOfVariableDependencies(42) == 2

    elem_dep, independents, elem_indep, dep_kinds = fmu.getVariableDependencies(42)
    assert list(elem_dep) == [0, 1]
    assert list(independents) == [10, 20]
    assert list(elem_indep) == [0, 0]
    assert list(dep_kinds) == [1, 2]
