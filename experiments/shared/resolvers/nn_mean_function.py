from typing import Any, Callable, Dict, Union

import flax.linen as nn
import jax
import jax.numpy as jnp
from flax.core.frozen_dict import FrozenDict

from experiments.shared.resolvers.nn_layer import nn_layer_resolver


def nn_mean_function_resolver(
    nn_mean_function_kwargs: Union[FrozenDict, Dict],
) -> Union[Callable[[Any, jnp.ndarray], jnp.ndarray], Any]:
    assert "layers" in nn_mean_function_kwargs, "Layers must be specified."

    class NeuralNetwork(nn.Module):
        @nn.compact
        def __call__(self, x):
            for layer in nn_mean_function_kwargs["layers"]:
                layer_params = nn_mean_function_kwargs["layers"][layer]
                assert (
                    "layer_scheme" in layer_params
                ), f"Layer scheme must be specified for {layer=}."
                assert (
                    "layer_kwargs" in layer_params
                ), f"Layer kwargs must be specified for {layer=}."
                x = nn_layer_resolver(
                    x=x,
                    nn_layer_scheme=layer_params["layer_scheme"],
                    nn_layer_kwargs=layer_params["layer_kwargs"],
                )
            return x.reshape(-1)

    neural_network = NeuralNetwork()

    assert (
        "seed" in nn_mean_function_kwargs
    ), "Seed must be specified for parameter initialisation."
    assert "input_shape" in nn_mean_function_kwargs, "Input shape must be specified."
    neural_network_parameters = neural_network.init(
        jax.random.PRNGKey(nn_mean_function_kwargs["seed"]),
        jnp.empty((1, *nn_mean_function_kwargs["input_shape"])),
    )
    return (
        lambda parameters, x: neural_network.apply(parameters, x),
        neural_network_parameters,
    )
