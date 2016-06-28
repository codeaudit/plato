from plato.tools.common.online_predictors import GradientBasedPredictor
from plato.tools.common.training import assess_online_symbolic_predictor
from plato.tools.convnet.conv_specifiers import ConvInitSpec, NonlinearitySpec, PoolerSpec
from plato.tools.convnet.convnet import ConvNet
from plato.tools.optimization.cost import negative_log_likelihood_dangerous
from plato.tools.optimization.optimizers import AdaMax
from utils.benchmarks.train_and_test import percent_argmax_correct
from utils.datasets.cifar import get_cifar_10_dataset
import pickle
import numpy as np

__author__ = 'peter'


def test_convnet_serialization():

    cifar10 = get_cifar_10_dataset(normalize_inputs=True, n_training_samples=50, n_test_samples=50)
    test_epochs = [0, 1, 2]
    assert cifar10.input_shape == (3, 32, 32)

    net = ConvNet.from_init(
        input_shape = cifar10.input_shape,
        w_init=0.01,
        specifiers=[
            ConvInitSpec(n_maps = 24, filter_size = (3, 3), mode = 'same'),
            NonlinearitySpec('relu'),
            PoolerSpec(region = 2, stride=2, mode='max'), # (16x16)
            ConvInitSpec(n_maps = 48, filter_size = (3, 3), mode = 'same'),
            NonlinearitySpec('relu'),
            PoolerSpec(region = 2, stride=2, mode='max'), # (8x8)
            ConvInitSpec(n_maps = 96, filter_size = (3, 3), mode = 'same'),
            NonlinearitySpec('relu'),
            PoolerSpec(region = 2, stride=2, mode='max'), # (4x4),
            ConvInitSpec(n_maps = 192, filter_size = (4, 4), mode = 'valid'), # (1x1)
            NonlinearitySpec('relu'),
            ConvInitSpec(n_maps = 10, filter_size = (1, 1), mode = 'valid'),
            NonlinearitySpec('softmax'),
            ],
        )

    predictor = GradientBasedPredictor(
        function = net,
        cost_function=negative_log_likelihood_dangerous,
        optimizer=AdaMax()
        )

    assess_online_symbolic_predictor(
        predictor = predictor,
        dataset = cifar10,
        evaluation_function=percent_argmax_correct,
        test_epochs=test_epochs,
        minibatch_size=20,
        add_test_values = False
        )

    results_1 = net.compile()(cifar10.test_set.input)

    savable = net.to_spec()
    serialized = pickle.dumps(savable)
    deserialized = pickle.loads(serialized)

    net_2 = ConvNet.from_init(deserialized,input_shape=cifar10.input_shape, rng=None)
    results_2 = net_2.compile()(cifar10.test_set.input)
    assert np.array_equal(results_1, results_2)


if __name__ == '__main__':
    test_convnet_serialization()
