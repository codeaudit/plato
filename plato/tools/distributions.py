import theano.tensor as tt

__author__ = 'peter'


raise NotImplementedError('Under Construction...')


class Gaussian(object):

    def __init__(self, mean, covariance):
        self._mean = mean
        self._covariance = covariance

    def likelihood(self, point):
        pass


