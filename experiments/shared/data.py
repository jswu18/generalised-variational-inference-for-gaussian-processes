import os
from dataclasses import dataclass
from typing import Optional

import jax
from jax import numpy as jnp
from sklearn.model_selection import train_test_split

from src.utils.custom_types import PRNGKey


@dataclass
class Data:
    x: jnp.ndarray
    y: jnp.ndarray
    name: str = "data"

    def __add__(self, other):
        return Data(
            name=self.name + other.name,
            x=jnp.concatenate([self.x, other.x], axis=0),
            y=jnp.concatenate([self.y, other.y], axis=0),
        )

    def save(self, path: str):
        jnp.savez(os.path.join(path, f"{self.name}.npz"), x=self.x, y=self.y)

    @staticmethod
    def load(path: str, name: str):
        data_path = os.path.join(path, f"{name}.npz")
        if os.path.isfile(data_path):
            data = jnp.load(data_path)
            return Data(name=name, x=jnp.array(data["x"]), y=jnp.array(data["y"]))
        else:
            return None


@dataclass
class ExperimentData:
    name: str
    full: Data
    train: Optional[Data] = None
    test: Optional[Data] = None
    validation: Optional[Data] = None

    @staticmethod
    def _add_with_none(a: Optional[Data], b: Optional[Data]) -> Optional[Data]:
        if a is None and b is None:
            return None
        elif a is None:
            return b
        elif b is None:
            return a
        else:
            return a + b

    def __add__(self, other):
        return ExperimentData(
            name=self.name + other.name,
            full=self._add_with_none(self.full, other.full),
            train=self._add_with_none(self.train, other.train),
            test=self._add_with_none(self.test, other.test),
            validation=self._add_with_none(self.validation, other.validation),
        )

    def save(self, path: str):
        save_path = os.path.join(path, self.name)
        os.makedirs(save_path, exist_ok=True)
        self.full.name = "full"
        self.full.save(save_path)
        if self.train is not None:
            self.train.name = "train"
            self.train.save(save_path)
        if self.test is not None:
            self.test.name = "test"
            self.test.save(save_path)
        if self.validation is not None:
            self.validation.name = "validation"
            self.validation.save(save_path)

    @staticmethod
    def load(path: str, name: str):
        data_dir = os.path.join(path, name)
        return ExperimentData(
            name=name,
            full=Data.load(path=data_dir, name="full"),
            train=Data.load(path=data_dir, name="train"),
            test=Data.load(path=data_dir, name="test"),
            validation=Data.load(path=data_dir, name="validation"),
        )


def set_up_experiment(
    name: str,
    key: PRNGKey,
    x: jnp.ndarray,
    y: jnp.ndarray,
    train_data_percentage: float,
    test_data_percentage: float,
    validation_data_percentage: float,
) -> ExperimentData:
    # adapted from https://datascience.stackexchange.com/questions/15135/train-test-validation-set-splitting-in-sklearn
    key, subkey = jax.random.split(key)
    (
        x_train,
        x_test_and_validation,
        y_train,
        y_test_and_validation,
    ) = train_test_split(
        x,
        y,
        test_size=1 - train_data_percentage,
        random_state=int(jnp.sum(subkey)) % (2**32 - 1),
    )

    key, subkey = jax.random.split(key)
    x_validation, x_test, y_validation, y_test = train_test_split(
        x_test_and_validation,
        y_test_and_validation,
        test_size=test_data_percentage
        / (test_data_percentage + validation_data_percentage),
        random_state=int(jnp.sum(subkey)) % (2**32 - 1),
    )
    experiment_data = ExperimentData(
        name=name,
        full=Data(x=x, y=y),
        train=Data(x=x_train, y=y_train),
        test=Data(x=x_test, y=y_test),
        validation=Data(x=x_validation, y=y_validation),
    )
    return experiment_data
