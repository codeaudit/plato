from general.should_be_builtins import all_equal
import numpy as np

__author__ = 'peter'


class DataSet(object):

    def __init__(self, training_set, test_set, validation_set = None, name = None):

        sets = [training_set, test_set] + [validation_set] if validation_set is not None else []
        assert all_equal(*[[x.shape[1:] for x in s.inputs] for s in sets])
        assert all_equal(*[[x.shape[1:] for x in s.targets] for s in sets])
        self.training_set = training_set
        self.test_set = test_set
        self._validation_set = validation_set
        self._name = name

    @property
    def validation_set(self):
        if self._validation_set is None:
            raise Exception('Validation set does not exist')
        else:
            return self._validation_set

    @property
    def input_shapes(self):
        return [x.shape[1:] for x in self.training_set.inputs]

    @property
    def input_shape(self):
        return self.training_set.input.shape[1:]

    @property
    def target_shapes(self):
        return [x.shape[1:] for x in self.training_set.targets]

    @property
    def target_shape(self):
        return self.training_set.target.shape[1:]

    @property
    def name(self):
        return self.__class__.__name__ if self._name is None else self._name

    @property
    def xyxy(self):
        """
        Shorthand to return (input_of_training_set, targets_of_training_set, input_of_test_set, targets_of_test_set)
        :return:
        """
        return self.training_set.input, self.training_set.target, self.test_set.input, self.test_set.target

    def process_with(self, inputs_processor=None, targets_processor = None):
        return DataSet(
            training_set=self.training_set.process_with(inputs_processor, targets_processor),
            test_set=self.test_set.process_with(inputs_processor, targets_processor),
            validation_set=self._validation_set.process_with(inputs_processor, targets_processor) if self._validation_set is not None else None,
        )

    @staticmethod
    def from_xyxy(training_inputs, training_targets, test_inputs, test_targets):
        return DataSet(training_set = DataCollection(training_inputs, training_targets), test_set = DataCollection(test_inputs, test_targets))

    def __repr__(self):
        return '<%s with %s training samples, %s test samples, input_shapes = %s, target_shapes = %s at %s>' \
            % (self.name, self.training_set.n_samples, self.test_set.n_samples,
               [x.shape[1:] for x in self.training_set.inputs], [x.shape[1:] for x in self.training_set.targets],
                hex(id(self))
            )


class DataCollection(object):

    def __init__(self, inputs, targets):
        if isinstance(inputs, np.ndarray):
            inputs = (inputs, )
        if isinstance(targets, np.ndarray):
            targets = (targets, )
        n_samples = len(inputs[0])
        assert all(n_samples == len(d) for d in inputs) and all(n_samples == len(l) for l in targets)
        self._inputs = inputs
        self._targets = targets
        self._n_samples = n_samples

    @property
    def n_samples(self):
        return self._n_samples

    @property
    def inputs(self):
        return self._inputs

    @property
    def targets(self):
        return self._targets

    @property
    def input(self):
        only_input, = self._inputs
        return only_input

    @property
    def target(self):
        only_target, = self._targets
        return only_target

    def minibatch_iterator(self, **kwargs):
        """
        See minibatch_iterator
        """
        return minibatch_iterator(**kwargs)(self)

    def process_with(self, inputs_processor=None, targets_processor = None):
        inputs = inputs_processor(self._inputs) if inputs_processor is not None else self._inputs
        targets = targets_processor(self._targets) if targets_processor is not None else self._targets
        return DataCollection(inputs, targets)

def minibatch_iterator(minibatch_size = 1, epochs = 1, final_treatment = 'stop', single_channel = False):
    """
    :param minibatch_size:
    :param epochs:
    :param final_treatment:
    :param single_channel:
    :return: A function that, when called with a Data Collection, returns an iterator.
    """

    def iterator(data_collection):
        """
        :param data_collection: A DataCollection object
        :yield: A 2-tuple of (input_data, label_data)
        """
        assert isinstance(data_collection, DataCollection)
        i = 0
        n_samples = data_collection.n_samples
        total_samples = epochs * n_samples

        true_minibatch_size = n_samples if minibatch_size == 'all' else minibatch_size

        if single_channel:
            input_data = data_collection.input
            target_data = data_collection.target
        else:
            input_data = data_collection.inputs
            target_data = data_collection.targets

        while i < total_samples:
            next_i = i + true_minibatch_size
            segment = np.arange(i, next_i) % n_samples
            if next_i > total_samples:
                if final_treatment == 'stop':
                    break
                elif final_treatment == 'truncate':
                    next_i = total_samples
                else:
                    raise Exception('Unknown final treatment: %s' % final_treatment)
            if single_channel:
                input_minibatch = input_data[segment]
                target_minibatch = target_data[segment]
            else:
                input_minibatch, = [d[segment] for d in input_data]
                target_minibatch, = [d[segment] for d in target_data]

            yield next_i, input_minibatch, target_minibatch
            i = next_i

    return iterator
