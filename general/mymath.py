import numpy as np
from scipy.stats import norm
__author__ = 'peter'

# Note - this module used to be called math, but it somehow results in a numpy import error
# due to some kind of name conflict with another module called math.

sigm = lambda x: 1/(1+np.exp(-x))


def cummean(x, axis = None):
    if axis is None:
        
    x=np.array(x)
    normalized = np.arange(1, x.shape[axis]+1).astype(float)[(slice(None), )+(None, )*(x.ndim-axis-1)]
    return np.cumsum(x, axis)/normalized


def cumvar(x, axis):
    """
    :return: Cumulative variance along axis
    """
    ex_2 = cummean(x, axis=axis)**2
    e_x2 = cummean(x**2, axis=axis)
    return e_x2-ex_2


def binary_permutations(n_bits):
    """
    Given some number of bits, return a shape (2**n_bits, n_bits) boolean array containing every permoutation
    of those bits as a row.
    :param n_bits: An integer number of bits
    :return: A shape (2**n_bits, n_bits) boolean array containing every permoutation
        of those bits as a row.
    """
    return np.right_shift(np.arange(2**n_bits)[:, None], np.arange(n_bits-1, -1, -1)[None, :]) & 1


def softmax(x, axis = None):
    """
    The softmax function takes an ndarray, and returns an ndarray of the same size,
    with the softmax function applied along the given axis.  It should always be the
    case that np.allclose(np.sum(softmax(x, axis), axis)==1)
    """
    if axis is None:
        assert x.ndim==1, "You need to specify the axis for softmax if your data is more thn 1-D"
        axis = 0
    x = x - np.max(x, axis=axis, keepdims=True)  # For numerical stability - has no effect mathematically
    expx = np.exp(x)
    return expx/np.sum(expx, axis=axis, keepdims=True)


def expected_sigm_of_norm(mean, std, method = 'maclauren-2'):
    """
    Approximate the expected value of the sigmoid of a normal distribution.

    Thanks go to this guy:
    http://math.stackexchange.com/questions/207861/expected-value-of-applying-the-sigmoid-function-to-a-normal-distribution

    :param mean: Mean of the normal distribution
    :param std: Standard Deviation of the normal distribution
    :return: An approximation to Expectation(sigm(N(mu, sigma**2)))
    """
    if method == 'maclauren-2':
        eu = np.exp(-mean)
        approx_exp = 1/(eu+1) + 0.5*(eu-1)*eu/((eu+1)**3) * std**2
        return np.minimum(np.maximum(approx_exp, 0), 1)

    elif method == 'maclauren-3':
        eu = np.exp(-mean)
        approx_exp = 1/(eu+1) + \
            0.5*(eu-1)*eu/((eu+1)**3) * std**2 + \
            (eu**3-11*eu**2+57*eu-1)/((8*(eu+1))**5) * std**4
        return np.minimum(np.maximum(approx_exp, 0), 1)
    elif method == 'probit':
        return norm.cdf(mean/np.sqrt(2.892 + std**2))
    else:
        raise Exception('Method "%s" not known' % method)
