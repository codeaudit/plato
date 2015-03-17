from abc import ABCMeta, abstractmethod
from plato.interfaces.decorators import symbolic_stateless
import theano.tensor as tt

__author__ = 'peter'


class ICostFunction(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, actual, target):
        """
        :param actual: An (n_samples x ...) tensor representing the actual output
        :param target: An (n_samples x ...) tensor representing the target output
        :return: A symbolic scalar representing the cost
        """

@symbolic_stateless
def softmax_negative_log_likelihood(actual, target):
    return negative_log_likelihood(tt.nnet.softmax(actual), target)


@symbolic_stateless
def negative_log_likelihood(actual, target):
    """
    :param actual: An (n_samples, n_labels) tensor where rows are normalized and actual[i,j] indicates the belief
        that on sample[i] the correct target is j.
    :param target: An (n_samples, ) tensor indicating the target label for each sample
    :return: The average (over samples) of the negative log-likelihood.
    """
    # TODO: Assert that actual is (n_samples, n_categories) and normalized along n_categories
    return -tt.mean(tt.log(actual)[tt.arange(actual.shape[0]), target])


@symbolic_stateless
def mean_squared_error(actual, target):
    return tt.mean(tt.sum((actual-target)**2, axis = 1), axis = 0)


@symbolic_stateless
def percent_correct(actual, target):
    return tt.mean(tt.eq(tt.argmax(actual, axis=1), target), axis = 0) * 100
