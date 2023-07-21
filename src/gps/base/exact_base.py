from abc import ABC
from typing import Any

import jax.numpy as jnp

from src.distributions import Gaussian
from src.gps.base.base import GPBase, GPBaseParameters
from src.kernels.base import KernelBase
from src.means.base import MeanBase

PRNGKey = Any  # pylint: disable=invalid-name


class ExactGPBase(GPBase, ABC):
    def __init__(
        self, mean: MeanBase, kernel: KernelBase, x: jnp.ndarray, y: jnp.ndarray
    ):
        self.x = x
        self.y = y
        super().__init__(mean=mean, kernel=kernel)

    def _calculate_prediction_distribution(
        self,
        parameters: GPBaseParameters,
        x: jnp.ndarray,
        full_covariance: bool,
    ) -> Gaussian:
        return self.calculate_posterior_distribution(
            parameters=parameters,
            x_train=self.x,
            y_train=self.y,
            x=x,
            full_covariance=full_covariance,
        )
