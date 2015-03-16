from general.should_be_builtins import bad_value
from plato.interfaces.decorators import symbolic_updater, symbolic_standard, symbolic_stateless, SymbolicReturn
from plato.tools.optimizers import SimpleGradientDescent
from plato.tools.symbolic_graph import SymbolicGraph
import theano
from theano import tensor as tt
from utils.graph_utils import FactorGraph, InferencePath
import numpy as np


class DeepBeliefNet(object):

    def __init__(self, layers, bridges):
        assert all(src in layers and dest in layers for src, dest in bridges.viewkeys()), \
            'All bridges must project to and from layers'
        self._graph = FactorGraph(variables=layers, factors=bridges)
        self._layers = layers
        self._bridges = bridges

    def get_inference_function(self, input_layers, output_layers, path=None, smooth = False):

        input_layers = input_layers if isinstance(input_layers, (list, tuple)) else (input_layers, )
        output_layers = output_layers if isinstance(output_layers, (list, tuple)) else (output_layers, )

        execution_path = \
            self._graph.get_execution_path(InferencePath(path, default_smooth=smooth)) if path is not None else \
            self._graph.get_execution_path_from_io(input_layers, output_layers, default_smooth=smooth)

        @symbolic_standard
        def inference_fcn(*input_signals):
            initial_signal_dict = {lay: sig for lay, sig in zip(input_layers, input_signals)}
            computed_signal_dict = execution_path.execute(initial_signal_dict)
            return SymbolicReturn(outputs = [computed_signal_dict[lay] for lay in output_layers], updates = [])

        return inference_fcn

    def get_constrastive_divergence_function(self, visible_layers, hidden_layers, input_layers = None, up_path = None, n_gibbs = 1, persistent = False,
            optimizer = SimpleGradientDescent(eta = 0.1)):

        visible_layers = visible_layers if isinstance(visible_layers, (list, tuple)) else (visible_layers, )
        hidden_layers = hidden_layers if isinstance(hidden_layers, (list, tuple)) else (hidden_layers, )
        if input_layers is None:
            assert set(visible_layers).issubset(self._graph.get_input_variables()), "If you don't specify input layers, "\
                "the visible layers must be inputs to the graph.  But they are not.  Visible layers: %s, Input layers: %s" \
                % (visible_layers, self._graph.get_input_variables().keys())

        elif up_path is None:
            up_path = self.get_inference_function(input_layers = input_layers, output_layers = visible_layers)
        else:
            up_path = self._graph.get_execution_path(up_path)

        # input_layers = visible_layers if input_layers is None else input_layers if isinstance(input_layers, (list, tuple)) else (input_layers, )

        propup = self.get_inference_function(visible_layers, hidden_layers)
        free_energy = self.get_free_energy_function(visible_layers, hidden_layers)

        @symbolic_updater
        def cd_function(*input_signals):

            if input_layers is None:
                wake_visible = input_signals
            else:
                wake_visible, _ = up_path(*input_signals)
            wake_hidden, _ = propup(*wake_visible)

            initial_hidden =[theano.shared(np.zeros(wh.tag.test_value.shape, dtype = theano.config.floatX), name = 'persistent_hidden_state') for wh in wake_hidden] \
                if persistent else wake_hidden

            gibbs_path = [(hidden_layers, visible_layers)] + [(visible_layers, hidden_layers), (hidden_layers, visible_layers)] * (n_gibbs-1)
            sleep_visible, _ = self.get_inference_function(hidden_layers, visible_layers, gibbs_path)(*initial_hidden)
            sleep_hidden, _ = propup(*sleep_visible)

            free_energy_difference = free_energy(*wake_visible).mean() - free_energy(*sleep_visible).mean()

            all_params = sum([x.parameters for x in ([self._layers[i] for i in visible_layers]
                +[self._layers[i] for i in hidden_layers]+[self._bridges[i, j] for i in visible_layers for j in hidden_layers])], [])

            updates = optimizer(cost = free_energy_difference, parameters = all_params, constants = wake_visible+sleep_visible)

            if persistent:
                updates += [(p, s) for p, s in zip(initial_hidden, sleep_hidden)]

            return updates

        return cd_function

    def get_free_energy_function(self, visible_layers, hidden_layers):
        """
        :param visible_layers:
        :param hidden_layers:
        :return: A s
        """

        # TODO: Verify that computation is correct for all choices of vis/hidden layers
        # http://www.iro.umontreal.ca/~lisa/twiki/bin/view.cgi/Public/DBNEquations

        visible_layers = visible_layers if isinstance(visible_layers, (list, tuple)) else (visible_layers, )
        hidden_layers = hidden_layers if isinstance(hidden_layers, (list, tuple)) else (hidden_layers, )

        bridges = {(src, dest): b for (src, dest), b in self._bridges.iteritems() if src in visible_layers and dest in hidden_layers}

        @symbolic_stateless
        def free_energy(*visible_signals):
            """
            :param visible_signals: The inputs to the visible layer, each of shape (n_samples, n_dims)
            :return: A float vector representing the free energy of each sample.
            """
            visible_signals = {lay: sig for lay, sig in zip(visible_layers, visible_signals)}
            hidden_currents = {hid: sum([b(visible_signals[src]) for (src, dest), b in bridges.iteritems() if dest == hid]) for hid in hidden_layers}
            visible_contributions = [b.free_energy(visible_signals[src]) for (src, dest), b in bridges.iteritems()]
            hidden_contributions = [self._layers[hid].free_energy(hidden_currents[hid]) for hid in hidden_layers]
            # Note: Need to add another term for Gaussian RBMs, which have a the sigma parameter attached to the visible layer
            return sum(visible_contributions+hidden_contributions)

        return free_energy

    # def get_training_function(self, visible_layer_ds, hidden_layer_ids, input_layer_ids = None,
    #         n_gibbs=1, persistent = False, optimizer = SimpleGradientDescent(eta = 0.01)):
    #     pass
    #
    #
# def _build_dbn_graph(layers, bridges):
#     graph_specifier = {}
#     bridge_namer = lambda src, dest: 'bridge[%s,%s]' % (src, dest)
#     for (src_layer_id, dest_layer_id), b in bridges:
#         bridge_out_id = bridge_namer(src_layer_id, dest_layer_id)
#         graph_specifier[src_layer_id, bridge_out_id] = b
#         graph_specifier[bridge_out_id, src_layer_id] = b.reverse
#     for layer_id, layer in layers:
#         graph_specifier[tuple(bridge_namer(s, d) for s, d in bridges if d == layer_id), layer_id] = layer
#     return SymbolicGraph(graph_specifier)
