__author__ = 'peter'
import numpy as np


def multichannel(fcn):
    """
    Take a function that accepts input arrays.

    This is a temporary thing until we have a proper decorator system for these array
    functions.

    :param fcn: A function of the form
        out_arr = fcn(in_arr_0, in_arr_1, ...)
    :return: A function of the form
        (out_arr, ) = fcn((in_arr_0, in_arr_1, ...))
    """
    return lambda args: (fcn(*args), )


def minibatch_iterate(data, minibatch_size, n_epochs):
    i = 0
    end = len(data)*n_epochs

    ixs = np.arange(minibatch_size)
    while ixs[0] < end:
        yield data[ixs]
        ixs+=minibatch_size
        ixs%=len(data)
