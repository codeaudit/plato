from plato.core import clear_tdb_traces
from plato.interfaces.decorators import symbolic_simple
from plato.tools.misc.tdb_plotting import tdbplot
from plotting.matplotlib_backend import ImagePlot, HistogramPlot
from theano.tensor.shared_randomstreams import RandomStreams
import numpy as np

__author__ = 'peter'


def test_tdb_plotting():

    @symbolic_simple
    def random_stuff():

        rng = RandomStreams(seed = None)

        a = rng.uniform((10, 10))
        b = rng.normal((10, 1))

        tdbplot(a, 'a', ImagePlot(cmap = 'jet'))
        tdbplot(b, 'b', HistogramPlot(edges = np.linspace(-5, 5, 20)))
        c = a+b
        return c

    f = random_stuff.compile()

    for _ in xrange(5):
        f()

    clear_tdb_traces()
    # Otherwise there's a weird thing wehre this keeps getting called for every
    # theano function call in this process..

if __name__ == '__main__':
    test_tdb_plotting()
