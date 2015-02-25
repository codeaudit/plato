from collections import OrderedDict
from general.nested_structures import flatten_struct
from plotting.data_conversion import vector_length_to_tile_dims
import plotting.matplotlib_backend as eplt

__author__ = 'peter'


def ezplot(anything, plots = None):
    """
    Make a plot of anything.  Anything at all.
    :param anything: Anything.
    """
    data_dict = flatten_struct(anything)
    plots = plot_data_dict(data_dict, plots, mode = 'static')
    return plots


def plot_data_dict(data_dict, plots = None, mode = 'static'):
    """
    Make a plot of data in the format defined in data_dict
    :param data_dict: dict<str: plottable_data>
    :param plots: Optionally, a dict of <key: IPlot> identifying the plot objects to use (keys should
        be the same as those in data_dict).
    :return: The plots (same ones you provided if you provided them)
    """

    assert mode in ('live', 'static')
    if isinstance(data_dict, list):
        assert all(len(d) == 2 for d in data_dict), "You can provide data as a list of 2 tuples of (plot_name, plot_data)"
        data_dict = OrderedDict(data_dict)

    if plots is None:
        plots = {k: eplt.get_plot_from_data(v, mode = mode) for k, v in data_dict.iteritems()}

    eplt.figure()
    n_rows, n_cols = vector_length_to_tile_dims(len(data_dict))
    for i, (k, v) in enumerate(data_dict.iteritems()):
        eplt.subplot(n_rows, n_cols, i+1)
        plots[k].update(v)
        eplt.title(k, fontdict = {'fontsize': 8})
    eplt.show()

    return plots
