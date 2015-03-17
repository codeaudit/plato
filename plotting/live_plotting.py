from collections import namedtuple, OrderedDict
from abc import abstractmethod
from general.nested_structures import flatten_struct
from plotting.easy_plotting import plot_data_dict
import plotting.matplotlib_backend as eplt


__author__ = 'peter'


class BaseStream(object):

    def __init__(self, update_every = 1):
        self._plots = None
        self._counter = -1
        self._update_every = update_every
        self._plot_keys = None
        self._fig = None

    def update(self):
        self._counter += 1
        if self._counter % self._update_every != 0:
            return

        data_dict = self._get_data_structure()

        if self._plots is None or set(data_dict.keys()) != self._plot_keys:
            # Note - this causes us to reset all plots (including ones with history
            # every time a new plot comes in, but that's ok for now).
            if self._fig is not None:
                self._fig.clf()
            else:
                self._fig = eplt.figure()
            self._plots = self._get_plots_from_first_data(data_dict)
            self._plot_keys = set(self._plots.keys())
            plot_data_dict(data_dict, plots = self._plots, hang = False, figure = self._fig)
        else:
            for k, v in data_dict.iteritems():
                self._plots[k].update(v)
        # self._fig.draw()
        eplt.draw()

    @abstractmethod
    def _get_data_structure(self):
        """
        :return a dict<str: data> where data is some form of plottable data
        """

    @abstractmethod
    def _get_plots_from_first_data(self, first_data):
        """
        :return: a dict<str: IPlot> containing the plots corresponding to each element of the data.
        """


class LiveStream(BaseStream):
    """
    Lets you automatically generate live plots from some arbitrary data structure returned by a callback.
    """

    def __init__(self, callback, custom_handlers = {}, plot_mode = 'live', **kwargs):
        """
        :param callback: Some function that takes no arguments and returns some object.
        """
        assert hasattr(callback, '__call__'), 'Your callback must be callable.'
        self._callback = callback
        self._custom_handlers=custom_handlers
        self._plot_mode = plot_mode
        BaseStream.__init__(self, **kwargs)

    def _get_data_structure(self):
        struct = self._callback()
        assert struct is not None, 'Your plotting-data callback returned None.  Probably you forgot to include a return statememnt.'

        flat_struct = flatten_struct(struct, custom_handlers=self._custom_handlers)  # list<*tuple<str, data>>
        return OrderedDict(flat_struct)

    def _get_plots_from_first_data(self, first_data):
        return {k: eplt.get_plot_from_data(v, mode = self._plot_mode) for k, v in first_data.iteritems()}


LivePlot = namedtuple('PlotBuilder', ['plot', 'cb'])


class LiveCanal(BaseStream):
    """
    Lets you make live plots by defining a dict of LivePlot objects, which contain the plot type and the data callback.
    LiveCanal gives you more control over your plots than LiveStream
    """

    def __init__(self, live_plots, **kwargs):
        """
        :param live_plots: A dict<str: (LivePlot OR function)>.  If the value is a LivePlot, you specify the type of
            plot to create.  Otherwise, you just specify a callback function, and the plot type is determined automatically
            based on the data.
        :param kwargs: Passed up to BaseStream
        """
        self._live_plots = live_plots
        self._callbacks = {k: lp.cb if isinstance(lp, LivePlot) else lp for k, lp in live_plots.iteritems()}
        BaseStream.__init__(self, **kwargs)

    def _get_data_structure(self):
        return {k: cb() for k, cb in self._callbacks.iteritems()}

    def _get_plots_from_first_data(self, first_data):
        # first_data = dict(first_data)
        return {k: pb.plot if isinstance(pb, LivePlot) else eplt.get_plot_from_data(first_data[k], mode = 'live') for k, pb in self._live_plots.iteritems()}
