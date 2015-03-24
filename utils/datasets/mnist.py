import pickle

from utils.datasets.datasets import DataSet, DataCollection
from fileman.file_getter import get_file, unzip_gz


__author__ = 'peter'


def get_mnist_dataset(n_training_samples = None, n_test_samples = None, flat = False):
    """
    The MNIST DataSet - the Drosophila of machine learning.

    :param n_training_samples: Cap on the number of training samples
    :param n_test_samples: Cap on the number of test samples
    :param flat: Set to True if we just want flat 784-dimensional input data instead of 28x28 images.
    :return: A DataSet object containing the MNIST data
    """
    filename = get_file(
        local_name = 'data/mnist.pkl',
        url = 'http://deeplearning.net/data/mnist/mnist.pkl.gz',
        data_transformation = unzip_gz)

    with open(filename) as f:
        data = pickle.load(f)

    x_tr, y_tr = data[0] if n_training_samples is None else (data[0][0][:n_training_samples], data[0][1][:n_training_samples])
    x_ts, y_ts = data[1] if n_test_samples is None else (data[1][0][:n_test_samples], data[1][1][:n_test_samples])
    x_vd, y_vd = data[2]
    if not flat:
        x_tr = x_tr.reshape(-1, 28, 28)
        x_ts = x_ts.reshape(-1, 28, 28)
        x_vd = x_vd.reshape(-1, 28, 28)
    return DataSet(training_set=DataCollection(x_tr, y_tr), test_set=DataCollection(x_ts, y_ts), validation_set=DataCollection(x_vd, y_vd))
