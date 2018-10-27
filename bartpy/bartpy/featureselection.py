import numpy as np
from sklearn.feature_selection.base import SelectorMixin
from sklearn.base import BaseEstimator

from bartpy.diagnostics.features import null_feature_split_proportions_distribution, \
    local_thresholds, global_thresholds, is_kept, feature_split_proportions_counter
from bartpy.sklearnmodel import SklearnModel


class SelectSplitProportionThreshold(BaseEstimator, SelectorMixin):

    def __init__(self,
                 model: SklearnModel,
                 percentile: float=0.2):
        self.model = model
        self.percentile = percentile

    def fit(self, X, y):
        self.model.fit(X, y)
        self.X, self.y = X, y
        self.feature_proportions = feature_split_proportions_counter(self.model.model_samples)
        return self

    def _get_support_mask(self):
        return np.array([proportion > self.percentile for proportion in self.feature_proportions.values()])


class SelectNullDistributionThreshold(BaseEstimator, SelectorMixin):

    def __init__(self,
                 model: SklearnModel,
                 percentile: float=0.95,
                 method="local",
                 n_permutations=10):
        if method == "local":
            self.method = local_thresholds
        elif method == "global":
            self.method = global_thresholds
        else:
            raise NotImplementedError("Currently only local and global methods are supported, found {}".format(self.method))
        self.model = model
        self.percentile = percentile
        self.n_permutations = n_permutations

    def fit(self, X, y):
        self.model.fit(X, y)
        self.X, self.y = X, y
        self.null_distribution = null_feature_split_proportions_distribution(self.model, X, y, self.n_permutations)
        self.thresholds = local_thresholds(self.null_distribution, self.percentile)
        self.feature_proportions = feature_split_proportions_counter(self.model.model_samples)
        return self

    def _get_support_mask(self):
        return np.array(is_kept(self.feature_proportions, self.thresholds))