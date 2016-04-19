__author__ = 'peter'
import numpy as np


def multichannel(fcn):
    """
    Take a function that accepts N args and returns a single argument, and wrap it as a
    function that takes a tuple of length N as an argument and returns a tuple of length
    1.

    This is a temporary thing until we have a proper decorator system for these array
    functions.

    :param fcn: A function of the form
        out_arr = fcn(in_arr_0, in_arr_1, ...)
    :return: A function of the form
        (out_arr, ) = fcn((in_arr_0, in_arr_1, ...))
    """
    return lambda args: (fcn(*args), )


def single_to_batch(fcn, *batch_inputs, **batch_kwargs):
    """
    :param fcn: A function
    :param batch_inputs: A collection of batch-form (n_samples, input_dims_i) inputs
    :return: batch_outputs, an (n_samples, output_dims) array
    """
    n_samples = len(batch_inputs[0])
    assert all(len(b) == n_samples for b in batch_inputs)
    first_out = fcn(*[b[0] for b in batch_inputs], **{k: b[0] for k, b in batch_kwargs.iteritems()})
    if n_samples==1:
        return first_out[None]
    out = np.empty((n_samples, )+first_out.shape)
    out[0] = n_samples
    for i in xrange(1, n_samples):
        out[i] = fcn(*[b[i] for b in batch_inputs], **{k: b[i] for k, b in batch_kwargs.iteritems()})
    return out


def kwarg_map(element_constructor, **kwarg_lists):
    """
    A helper function for when you want to construct a chain of objects with individual arguments for each one.  Can
    be easier to read than a list expansion.

    :param element_constructor: A function of the form object = fcn(**kwargs)
    :param kwarg_lists: A dict of lists, where the index identifies two which element its corresponding value will go.
    :return: A list of objects.

    e.g. Initializing a chain of layers:
        layer_sizes = [784, 240, 240, 10]
        layers = kwarg_map(
            Layer,
            n_in = layer_sizes[:-1],
            n_out = layer_sizes[1:],
            activation = ['tanh', 'tanh', 'softmax'],
            )

    is equivalent to:
        layers = [Layer(n_in=784, n_out=240, activation='tanh'), Layer(n_in=240, n_out=240, activation='tanh'), Layer(n_in=240, n_out=10, activation='softmax')]
    """
    all_lens = [len(v) for v in kwarg_lists.values()]
    assert len(kwarg_lists)>0, "You need to specify at least list of arguments (otherwise you don't need this function)"
    n_elements = all_lens[0]
    assert all(n_elements == le for le in all_lens), 'Inconsistent lengths: %s' % (all_lens, )
    return [element_constructor(**{k: v[i] for k, v in kwarg_lists.iteritems()}) for i in xrange(n_elements)]


def create_object_chain_complex(element_constructor, shared_args = {}, each_args = {}, paired_args = {}, n_elements = None):
    """
    * Slated for deletion unless we have use case.  See kwarg_map and see if that doesn't cover your needs.

    A helper function for when you want to construct a chain of objects.  Objects in the chain can either get
    the same arguments or individual arguments.

    :param element_constructor: A function of the form object = fcn(**kwargs)
    :param shared_args: A dict of kwargs that will be passed to all objects
    :param each_args: A dict of lists, where the index identifies two which element its corresponding value will go.
    :param paired_args: A dist of form {(arg_name_1, arg_name_2): [v1, v2, ...]}.  The length of the lists in this dictionary
        is one greater than the number of elements.  See example below for how this is used.
    :return: A list of objects.

    e.g. Initializing a chain of layers.

    layers = kwarg_map(
        element_constructor = lambda n_in, n_out, activation: Layer(n_in, n_out, activation, rng),
        shared_args = dict(rng = np.random.RandomState(1234)),
        each_args = dict(activation = ['tanh', 'tanh', 'softmax'],
        paired_args = dict(('n_in', 'n_out'): [784, 240, 240, 10])
        )
    """

    all_lens = [len(v) for v in each_args.values()]+[len(v)-1 for v in paired_args.values()]
    assert len(all_lens)>0, 'You need to specify at least one "each_args" or "paired args'
    if n_elements is None:
        n_elements = all_lens[0]
    assert all(n_elements == le for le in all_lens), 'Inconsistent lengths: %s' % (all_lens)
    return [element_constructor(
            **dict(
                shared_args.items() +
                {k: v[i] for k, v in each_args.iteritems()}.items() +
                {k0: v[i] for (k0, k1), v in paired_args.iteritems()}.items() +
                {k1: v[i+1] for (k0, k1), v in paired_args.iteritems()}.items())
            ) for i in xrange(n_elements)]
