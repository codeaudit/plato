from collections import namedtuple
from artemis.general.should_be_builtins import bad_value
import numpy as np

__author__ = 'peter'


def minibatch_index_generator(n_samples, minibatch_size, n_epochs = 1, final_treatment = 'stop', slice_when_possible = True):
    """
    Generates the indices for minibatch-iteration.

    :param n_samples: Number of samples in the data you want to iterate through
    :param minibatch_size: Number of samples in the minibatch
    :param n_epochs: Number of epochs to iterate for
    :param final_treatment: How to terminate.  Options are:
        'stop': Stop when you can no longer get a complete minibatch
        'truncate': Produce a runt-minibatch at the end.
    :param slice_when_possible: Return slices, instead of indices, as long as the indexing does not wrap around.  This
        can be more efficient, since it avoids array copying, but you have to be careful not to modify your source array.
    :yield: IIndices that you can use to slice arrays for minibatch iteration.
    """

    true_minibatch_size = n_samples if minibatch_size == 'full' else \
        minibatch_size if isinstance(minibatch_size, int) else \
        bad_value(minibatch_size)
    remaining_samples = int(n_epochs * n_samples) if not np.isinf(n_epochs) else np.inf
    base_indices = np.arange(minibatch_size)
    standard_indices = (lambda: slice(i, i+minibatch_size)) if slice_when_possible else (lambda: base_indices+i)
    i = 0
    while True:
        next_i = i + true_minibatch_size
        if remaining_samples < minibatch_size:  # Final minibatch case
            if final_treatment == 'stop':
                break
            elif final_treatment == 'truncate':
                yield np.arange(i, i+remaining_samples) % n_samples
                break
            else:
                raise Exception('Unknown final treatment: %s' % final_treatment)
        elif next_i < n_samples:  # Standard case
            segment = standard_indices()
        else:  # Wraparound case
            segment = np.arange(i, next_i) % n_samples
            next_i = next_i % n_samples

        yield segment
        i = next_i
        remaining_samples -= minibatch_size


def checkpoint_minibatch_index_generator(n_samples, checkpoints, slice_when_possible = True):
    """
    Generates minibatch indices that fill the space between checkpoints.  This is useful, for instance, when you want to test
    at certain points, and your predictor internally iterates through the minibatch sample by sample between those.
    :param n_samples: Number of samples in the data you want to iterate through
    :param checkpoints: An array of indices at which the "checkpoints" happen.  Minibatches will be sliced up by these
        indices.
    :param slice_when_possible: Return slices, instead of indices, as long as the indexing does not wrap around.  This
        can be more efficient, since it avoids array copying, but you have to be careful not to modify your source array.
    :yield: Indices that you can use to slice arrays for minibatch iteration.
    """
    checkpoints = np.array(checkpoints, dtype = int)
    assert len(checkpoints) > 1 and checkpoints[0] >= 0 and np.all(np.diff(checkpoints) > 0)
    checkpoint_divs = zip(checkpoints[:-1], checkpoints[1:])
    if checkpoints[0] > 0:
        checkpoint_divs.insert(0, (0, checkpoints[0]))
    for start, stop in checkpoint_divs:
        if start/n_samples == stop/n_samples:  # No wrap
            if slice_when_possible:
                yield slice(start % n_samples, stop % n_samples)
            else:
                yield np.arange(start % n_samples, stop % n_samples)
        else:
            yield np.arange(start, stop) % n_samples


def zip_minibatch_iterate(arrays, minibatch_size, n_epochs=1):
    """
    Yields minibatches from each array in arrays in sequence.
    :param arrays: A collection of arrays, all of which must have the same shape[0]
    :param minibatch_size: The number of samples per minibatch
    :param n_epochs: The number of epochs to run for
    :yield: len(arrays) arrays, each of shape: (minibatch_size, )+arr.shape[1:]
    """
    assert isinstance(arrays, (list, tuple)), 'Need at least one array' and len(arrays)>0
    total_size = arrays[0].shape[0]
    assert all(a.shape[0] == total_size for a in arrays), 'All arrays must have the same length!  Lengths are: %s' % ([len(arr) for arr in arrays])
    end = total_size*n_epochs
    ixs = np.arange(minibatch_size)
    while ixs[0] < end:
        yield tuple(a[ixs % total_size] for a in arrays)
        ixs+=minibatch_size


IterationInfo = namedtuple('IterationInfo', ['iteration', 'epoch', 'sample', 'time', 'test_now'])


def zip_minibatch_iterate_info(arrays, minibatch_size, n_epochs, test_epochs = None):
    """
    Iterate through minibatches of arrays and yield info about the state of iteration though training.

    :param arrays:
    :param arrays: A collection of arrays, all of which must have the same shape[0]
    :param minibatch_size: The number of samples per minibatch
    :param n_epochs: The number of epochs to run for
    :param test_epochs: A list of epochs to test at.
    :return: (array_minibatches, info)
        arrays is a tuple of minibatches from arrays
        info is an IterationInfo object returning information about the state of iteration.
    """
    import time
    n_samples = float(arrays[0].shape[0])
    next_text_point = 0 if test_epochs is not None and len(test_epochs)>0 else None
    start_time = time.time()
    for i, arrays in enumerate(zip_minibatch_iterate(arrays, minibatch_size=minibatch_size, n_epochs=n_epochs)):
        epoch = i*minibatch_size/n_samples
        test_now = (next_text_point is not None) and (epoch >= test_epochs[next_text_point])
        if test_now:
            next_text_point = next_text_point+1 if next_text_point < len(test_epochs)-1 else None
        info = IterationInfo(
            iteration = i,
            epoch = epoch,
            sample = i*minibatch_size,
            time = time.time()-start_time,
            test_now = test_now
            )
        yield arrays, info




def minibatch_iterate(data, minibatch_size, n_epochs=1):
    """
    Yields minibatches in sequence.
    :param data: A (n_samples, ...) data array
    :param minibatch_size: The number of samples per minibatch
    :param n_epochs: The number of epochs to run for
    :yield: (minibatch_size, ...) data arrays.
    """
    if minibatch_size == 'full':
        minibatch_size = len(data)
    end = len(data)*n_epochs
    ixs = np.arange(minibatch_size)
    while ixs[0] < end:
        yield data[ixs % len(data)]
        ixs+=minibatch_size
