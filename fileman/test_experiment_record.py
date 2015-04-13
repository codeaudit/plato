from general.test_mode import set_test_mode
import os
import pickle
from fileman.experiment_record import ExperimentRecord, start_experiment, run_experiment, show_experiment, \
    get_local_experiment_path
import numpy as np
import matplotlib.pyplot as plt


__author__ = 'peter'


def _run_experiment():

    print 'aaa'
    plt.figure('sensible defaults')
    dat = np.random.randn(4, 5)
    plt.subplot(211)
    plt.imshow(dat)
    plt.subplot(212)
    plt.imshow(dat, interpolation = 'nearest', cmap = 'gray')
    plt.show()
    print 'bbb'
    plt.plot(np.random.randn(10))
    plt.show()


def test_experiment_with():

    with ExperimentRecord(filename = 'test_exp') as exp_1:
        _run_experiment()

    assert exp_1.get_logs() == 'aaa\nbbb\n'
    figs = exp_1.show_figures()
    assert len(exp_1.get_figure_locs()) == 2

    # Now assert that you can load an experiment from file and again display the figures.
    exp_file = exp_1.get_file_path()
    with open(exp_file) as f:
        exp_1_copy = pickle.load(f)

    assert exp_1_copy.get_logs() == 'aaa\nbbb\n'
    exp_1_copy.show_figures()
    assert len(exp_1.get_figure_locs()) == 2


def test_start_experiment():
    """
    An alternative syntax to the with statement - less tidy but possibly better
    for notebooks and such because it avoids you having to indent all code in the
    experiment.
    """

    exp = start_experiment(save_result = False)
    _run_experiment()
    exp.end_and_show()
    assert len(exp.get_figure_locs()) == 2


def test_run_and_show():
    """
    This is nice because it no longer required that an experiment be run and shown in a
    single session - each experiment just has a unique identifier that can be used to show
    its results whenevs.
    """
    identifier = run_experiment('the_exp', exp_dict = {'the_exp': _run_experiment}, save_result = True)
    show_experiment(identifier)
    os.remove(get_local_experiment_path(identifier))


if __name__ == '__main__':

    set_test_mode(True)

    test_run_and_show()
    test_experiment_with()
    test_start_experiment()
