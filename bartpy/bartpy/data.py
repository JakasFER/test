from collections import namedtuple
from typing import Any, Set

import pandas as pd
import numpy as np

from bartpy.errors import NoSplittableVariableException


SplitData = namedtuple("SplitData", ["left_data", "right_data"])


class Data:
    """
    Encapsulates feature data
    Useful for providing cached access to commonly used functions of the data
    """

    def __init__(self, X: pd.DataFrame, y: np.ndarray, normalize=False, cache=True):
        self._X = X
        if normalize:
            self.original_y_min, self.original_y_max = y.min(), y.max()
            self._y = self.normalize_y(y)
        else:
            self._y = y
        if cache:
            self._n_unique_values = self._X.apply(pd.Series.nunique).to_dict()
            self._max_values = self._X.apply(np.max).to_dict()

    @property
    def y(self) -> np.ndarray:
        return self._y

    @property
    def X(self) -> pd.DataFrame:
        return self._X

    def splittable_variables(self) -> Set[str]:
        return {x for x in self._n_unique_values.keys() if self._n_unique_values[x] > 1}

    @property
    def variables(self) -> Set[str]:
        """
        The set of variable names the data contains.
        Of dimensionality p

        Returns
        -------
        Set[str]
        """
        return set(self.X.columns)

    def random_splittable_variable(self) -> str:
        """
        Choose a variable at random from the set of splittable variables
        Returns
        -------
            str - a variable name that can be split on
        """
        splittable_variables = list(self.splittable_variables())
        if len(splittable_variables) == 0:
            raise NoSplittableVariableException()
        return np.random.choice(np.array(list(splittable_variables)), 1)[0][0]

    def random_splittable_value(self, variable: str) -> Any:
        """
        Return a random value of a variable
        Useful for choosing a variable to split on

        Parameters
        ----------
        variable - str
            Name of the variable to split on

        Returns
        -------
        Any

        Notes
        -----
          - Won't create degenerate splits, all splits will have at least one row on both sides of the split
        """
        max_value = self._max_values[variable]
        candidate = np.random.choice(self.X[variable])
        while candidate == max_value:
            candidate = np.random.choice(self.X[variable])
        return candidate

    def unique_values(self, variable: str) -> Set[Any]:
        """
        Set of all values a variable takes in the feature set

        Parameters
        ----------
        variable - str
            name of the variable

        Returns
        -------
        Set[Any] - all possible values
        """
        return set(self.X[variable])

    @property
    def n_obsv(self) -> int:
        return len(self.X)

    @property
    def n_splittable_variables(self) -> int:
        return len(self.splittable_variables())

    def n_unique_values(self, variable: str) -> int:
        return self._n_unique_values[variable]

    @staticmethod
    def normalize_y(y: np.ndarray) -> np.ndarray:
        """
        Normalize y into the range (-0.5, 0.5)
        Useful for allowing the leaf parameter prior to be 0, and to standardize the sigma prior

        Parameters
        ----------
        y - np.ndarray

        Returns
        -------
        np.ndarray

        Examples
        --------
        >>> Data.normalize_y([1, 2, 3])
        array([-0.5,  0. ,  0.5])
        """
        y_min, y_max = np.min(y), np.max(y)
        return -0.5 + ((y - y_min) / (y_max - y_min))

    def unnormalize_y(self, y: np.ndarray) -> np.ndarray:
        distance_from_min = y - (-0.5)
        total_distance = (self.original_y_max - self.original_y_min)
        return self.original_y_min + (distance_from_min * total_distance)

    @property
    def unnormalized_y(self) -> np.ndarray:
        return self.unnormalize_y(self.y)

    @property
    def normalizing_scale(self) -> float:
        return self.original_y_max - self.original_y_min