import time
import matplotlib
matplotlib.use('Qt5Agg')
from plotting.live_plotting import LiveStream, LiveCanal, LivePlot
from plotting.matplotlib_backend import MovingImagePlot, MovingPointPlot, LinePlot, ImagePlot
from itertools import count

__author__ = 'peter'
import numpy as np


def test_streaming(duration = 10):
    # 8.9 FPS with default matplotlib backend

    c = count()

    stream = LiveStream(lambda: {
        'text': ['Veni', 'Vidi', 'Vici'][c.next() % 3],
        'images': {
            'bw_image': np.random.randn(20, 20),
            'col_image': np.random.randn(20, 20, 3),
            'vector_of_bw_images': np.random.randn(11, 20, 20),
            'vector_of_colour_images': np.random.randn(11, 20, 20, 3),
            'matrix_of_bw_images': np.random.randn(5, 6, 20, 20),
            'matrix_of_colour_images': np.random.randn(5, 6, 20, 20, 3),
            },
        'line': np.random.randn(20),
        'lines': np.random.randn(20, 3),
        'moving_point': np.random.randn(),
        'moving_points': np.random.randn(3),
        })

    for i in xrange(duration):
        if i==1:
            start_time = time.time()
        elif i>1:
            print 'Average Frame Rate: %.2f FPS' % (i/(time.time()-start_time), )
        stream.update()


def test_canaling(duration = 10):

    n_dims = 4

    # Don't be frightened by the double-lambda here - the point is just to get a callback
    # that spits out the same data when called in sequence.
    cb_constructor_1d = lambda: lambda rng = np.random.RandomState(0): rng.randn(n_dims)
    cb_image_data = lambda: lambda rng = np.random.RandomState(1): rng.rand(20, 30)
    cb_sinusoid_data = lambda: lambda c=count(): np.sin(c.next()/40.)

    canal = LiveCanal({
        '1d-default': cb_constructor_1d(),
        '1d-image': LivePlot(plot = MovingImagePlot(buffer_len=20), cb = cb_constructor_1d()),
        '1d-seizmic': LivePlot(plot = MovingPointPlot(), cb = cb_constructor_1d()),
        '1d-line': LivePlot(plot = LinePlot(), cb = cb_constructor_1d()),
        'image-autoscale': LivePlot(ImagePlot(), cb_image_data()),
        'image-overexposed': LivePlot(ImagePlot(scale = (0, 0.2)), cb_image_data()),
        'trace-default': cb_sinusoid_data(),
        'trace-prescaled': LivePlot(MovingPointPlot(yscale=(-1, 1)), cb_sinusoid_data()),
        })

    for i in xrange(duration):
        canal.update()


if __name__ == '__main__':

    test_streaming(500)
    # test_canaling(10)
