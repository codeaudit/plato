import logging
import numpy as np

__author__ = 'peter'

"""
All evaluation functions in here are of the form

score = evaluation_fcn(actual, target)

Where:
    score is a scalar
    actual is an (n_samples, ...) array
    target is an (n_samples, ....) array
"""


def train_online_predictor(predictor, training_set, iterator):
    logging.info('Training Predictor %s...' % (predictor, ))
    for (data, target) in iterator(training_set):
        predictor.train(data, target)
    logging.info('Done.')


def evaluate_predictor(predictor, test_set, evaluation_function):
    output = predictor.predict(test_set.input)
    score = evaluation_function(actual = output, target = test_set.target)
    return score


def get_evaluation_function(name):
    return {
        'mse': mean_squared_error,
        'mean_squared_error': mean_squared_error,
        'percent_argmax_correct': percent_argmax_correct,
        'percent_correct': percent_correct,
        }[name]


def mean_squared_error(actual, target):
    return np.mean(np.sum((actual-target)**2, axis = -1), axis = -1)


def fraction_correct(actual, target):
    return np.mean(actual == target)


def percent_correct(actual, target):
    return 100*fraction_correct(actual, target)


def percent_argmax_correct(actual, target):
    """
    :param actual: An (n_samples, n_dims) array
    :param target: An (n_samples, ) array of indices OR an (n_samples, n_dims) array
    :return:
    """
    assert actual.ndim == 2, 'percent_argmax_correct expects shape (n_samples, n_categories) labels.  Shape was %s' % (actual.shape, )
    if target.ndim == 2:
        target = np.argmax(target, axis = 1)
    else:
        assert target.ndim == 1

    return 100*fraction_correct(np.argmax(actual, axis = 1), target)
