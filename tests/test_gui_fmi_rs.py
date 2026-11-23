import numpy as np
import pytest

from fmpy import extract, read_model_description

pytest.importorskip('fmi_rs')
pytest.importorskip('PySide6')

from fmpy.gui.simulation import FmiRsSimulationThread, recorded_columns


@pytest.fixture
def bouncing_ball(reference_fmus_dist_dir, tmp_path):
    return extract(reference_fmus_dist_dir / '3.0' / 'BouncingBall.fmu', unzipdir=tmp_path / 'BouncingBall')


def create_thread(filename, **kwargs):
    args = dict(
        filename=filename,
        fmiType='CoSimulation',
        stopTime=3.0,
        solver='CVode',
        stepSize=1e-3,
        relativeTolerance=1e-6,
        outputInterval=0.1,
        startValues={},
        applyDefaultStartValues=False,
        input=None,
        output=None,
        debugLogging=False,
        fmiLogging=False,
    )
    args.update(kwargs)
    return FmiRsSimulationThread(**args)


def run(thread):
    messages = []
    progress = []
    thread.messageChanged.connect(lambda level, message: messages.append((level, message)))
    thread.progressChanged.connect(progress.append)
    thread.run()  # run synchronously
    return messages, progress


@pytest.mark.parametrize('fmi_type, solver', [('CoSimulation', 'CVode'), ('ModelExchange', 'Euler'), ('ModelExchange', 'CVode')])
def test_simulate(qtbot, bouncing_ball, fmi_type, solver):

    thread = create_thread(bouncing_ball, fmiType=fmi_type, solver=solver, startValues={'h': '2'})

    messages, progress = run(thread)

    assert not [m for m in messages if m[0] == 'error'], messages

    result = thread.result
    assert result['time'][-1] == pytest.approx(3)
    assert result['h'][0] == pytest.approx(2)
    assert progress[-1] >= 99  # progress = int(time / stopTime * 100)

    # the rows streamed during the simulation are plotted with these columns
    live = np.array(thread.rows, dtype=np.dtype(thread.cols))
    assert live.dtype.names == result.dtype.names
    assert np.array_equal(live['h'], result['h'])


def test_stop(qtbot, bouncing_ball):

    thread = create_thread(bouncing_ball)
    thread.stopped = True

    messages, _ = run(thread)

    assert len(thread.result) == 1
    assert messages[-1][1].startswith('Simulation stopped')


def test_error(qtbot, bouncing_ball):

    thread = create_thread(bouncing_ball, outputInterval=0.7)

    messages, _ = run(thread)

    assert any(level == 'error' and 'divisor' in message for level, message in messages)
    assert thread.result is None


def test_fmi_call_logging(qtbot, bouncing_ball):

    thread = create_thread(bouncing_ball, fmiLogging=True)

    messages, _ = run(thread)

    calls = [message for level, message in messages if level == 'debug']
    assert any(call.startswith('fmi3DoStep(') for call in calls)


def test_alias(qtbot, bouncing_ball):

    thread = create_thread(bouncing_ball)

    run(thread)

    # h_ft is an FMI 3.0 alias of h
    assert np.array_equal(thread.result['h_ft'], thread.result['h'])


def test_recorded_columns(reference_fmus_dist_dir):

    md = read_model_description(reference_fmus_dist_dir / '3.0' / 'StateSpace.fmu')
    cols = dict((c[0], c[1:]) for c in recorded_columns(md))

    assert 'time' in cols
    assert cols['y'][1] == (3,)


def test_engine_combo_box(qtbot):

    from fmpy.gui import compile_resources
    compile_resources()

    from fmpy.gui.MainWindow import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)

    engines = [window.engineComboBox.itemText(i) for i in range(window.engineComboBox.count())]
    assert engines == ['FMPy', 'fmi-rs']
