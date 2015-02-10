from abc import ABCMeta, abstractmethod
from plotting.data_conversion import put_data_in_grid, RecordBuffer, scale_data_to_8_bit

__author__ = 'peter'


from matplotlib.pyplot import *


class IPlot(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        pass


class ImagePlot(object):

    def __init__(self, cmap = 'gray', interpolation = 'nearest', show_axes = False):
        self._plot = None
        self._cmap = cmap
        self._interpolation = interpolation
        self._show_axes = show_axes

    def update(self, data):

        plottable_data = put_data_in_grid(data) \
            if not (data.ndim==2 or data.ndim==3 and data.shape[2]==3) else \
            scale_data_to_8_bit(data)

        if self._plot is None:
            self._plot = imshow(plottable_data, cmap = self._cmap, interpolation = self._interpolation)
            if not self._show_axes:
                # self._plot.axes.get_xaxis().set_visible(False)
                self._plot.axes.tick_params(labelbottom = 'off')
                self._plot.axes.get_yaxis().set_visible(False)
            # colorbar()
        else:
            self._plot.set_array(plottable_data)
            self._plot.axes.set_xlabel('%.2f - %.2f' % (np.min(data), np.max(data)))
            # self._plot.axes.get_caxis


class LinePlot(object):

    def __init__(self):
        self._plots = None
        self._oldlims = (float('inf'), -float('inf'))

    def update(self, data):

        lims = np.min(data), np.max(data)

        if self._plots is None:
            self._plots = plot(data)
        else:
            for p, d in zip(self._plots, data[None] if data.ndim==1 else data.T):
                p.set_ydata(d)
                if lims[0]!=self._oldlims[0] or lims[1]!=self._oldlims[1]:
                    p.axes.relim()
                    p.axes.autoscale_view()

        self._oldlims = lims


class MovingPointPlot(LinePlot):

    def __init__(self, buffer_len=100):
        LinePlot.__init__(self)
        self._buffer = RecordBuffer(buffer_len)

    def update(self, data):
        buffer_data = self._buffer(data)
        LinePlot.update(self, buffer_data)


def get_plot_from_data(data, line_to_image_threshold = 8):

    if np.isscalar(data) or data.ndim==1 and data.shape[0]<line_to_image_threshold:
        return MovingPointPlot()
    elif data.ndim == 1 or data.ndim==2 and data.shape[1]<line_to_image_threshold:
        return LinePlot()
    if data.ndim in (2, 3, 4, 5):
        return ImagePlot()
    else:
        raise NotImplementedError('We have no way to plot data of shape %s.  Make one!' % (data.shape, ))
