import logging
from typing import List, Dict, Optional, Callable

import dill
import numpy as np
from lime.lime_tabular import LimeTabularExplainer as OriginalLimeTabularExplainer

from xai.explainer.abstract_explainer import AbstractExplainer
from xai.explainer.explainer_exceptions import ExplainerUninitializedError

LOGGER = logging.getLogger(__name__)

NUM_TOP_FEATURES = 5


class LimeTabularExplainer(AbstractExplainer):

    def __init__(self):
        self.available_modes = ['classification', 'regression']
        super(AbstractExplainer, self).__init__()

    def build_explainer(self, training_data: np.ndarray,
                        mode: str,
                        training_labels: Optional[List[int]] = None,
                        column_names: Optional[List[str]] = None,
                        categorical_features: Optional[List[int]] = None,
                        dict_categorical_mapping: Optional[Dict[int, List[str]]] = None,
                        kernel_width: Optional[float] = None,
                        verbose: bool = False,
                        class_names: Optional[List[str]] = None,
                        feature_selection: str = 'auto',
                        discretize_continuous: bool = True,
                        discretizer: str = 'quartile',
                        sample_around_instance: bool = False,
                        random_state: Optional[int] = None):
        """
        Build the LIME tabular explainer.
        For now, the parameters used to instantiate this class are exactly those of
        lime.lime_tabular.LimeTabularExplainer. Original documentation can be found here:
        https://lime-ml.readthedocs.io/en/latest/lime.html#module-lime.lime_tabular

        Args:
            training_data (np.ndarray): 2d Numpy array representing the training data 
                (or some representative subset)
            mode (str): Whether the problem is 'classification' or 'regression'
            training_labels (list): Training labels, which can be used by the continuous feature
                discretizer
            column_names (list): The names of the columns of the training data
            categorical_features (list): Integer list indicating the indices of categorical features
            dict_categorical_mapping (dict): Mapping of integer index of categorical feature
                (same as from categorical_features) to a list of values for that column.
                So dict_categorical_mapping[x][y] is the yth value of column x.
            kernel_width (float): Width of the exponential kernel used in the LIME loss function
            verbose (bool): Control verbosity. If true, local prediction values of the LIME model
                are printed
            class_names (list): Class names (positional index corresponding to class index)
            feature_selection (str): Feature selection method. See original docs for more details
            discretize_continuous (True): Whether to discretize non-categorical features
            discretizer (str): Type of discretization. See original docs for more details
            sample_around_instance (True): if True, will sample continuous features
                in perturbed samples from a normal centered at the instance
                being explained. Otherwise, the normal is centered on the mean
                of the feature data.
            random_state (int): The random seed to generate random numbers during training

        Returns:
            None
        """

        if mode not in self.available_modes:
            LOGGER.error('Mode must be one of {}! Failed to build explainer'.format(
                self.available_modes))
            return

        self.explainer_object = OriginalLimeTabularExplainer(
            training_data=training_data,
            mode=mode,
            training_labels=training_labels,
            feature_names=column_names,
            categorical_features=categorical_features,
            categorical_names=dict_categorical_mapping,
            kernel_width=kernel_width,
            verbose=verbose,
            class_names=class_names,
            feature_selection=feature_selection,
            discretize_continuous=discretize_continuous,
            discretizer=discretizer,
            sample_around_instance=sample_around_instance,
            random_state=random_state
        )

    def explain_instance(self, predict_fn: Callable,
                         instance: np.ndarray,
                         labels: List = (1,),
                         top_labels: Optional[int] = None,
                         num_features: Optional[int] = NUM_TOP_FEATURES,
                         num_samples: int = 5000,
                         distance_metric: str = 'euclidean') -> List:
        """
        Explain a prediction instance using the LIME tabular explainer.
        Like with `build_explainer`, the parameters of `explain_instance` are exactly those of
        lime.lime_tabular.LimeTabularExplainer.explain_instance.
        More documentation can be found at:
        https://lime-ml.readthedocs.io/en/latest/lime.html#lime.lime_tabular.LimeTabularExplainer.explain_instance

        Args:
            predict_fn (Callable): A function that takes in a 1D numpy array and outputs a vector
                of probabilities which should sum to 1.
            instance (np.ndarray): A 1D numpy array corresponding to a row/single example
            labels (list): The list of class indexes to produce explanations for
            top_labels (int): If not None, this overwrites labels and the explainer instead produces
                explanations for the top k classes
            num_features (int): Number of features to include in an explanation
            num_samples (int): The number of perturbed samples to train the LIME model with
            distance_metric (str): The distance metric to use for weighting the loss function

        Returns:
            (list) A list of tuples of the form (feature_name, weight)

        Raises:
            ExplainerUninitializedError: Raised if self.explainer_object is None
        """
        if self.explainer_object:
            explanation = self.explainer_object.explain_instance(
                data_row=instance,
                predict_fn=predict_fn,
                labels=labels,
                top_labels=top_labels,
                num_features=num_features,
                num_samples=num_samples,
                distance_metric=distance_metric
            )
            return explanation.as_list()
        else:
            raise ExplainerUninitializedError('This explainer is not yet instantiated! '
                                              'Please call build_explainer()'
                                              'first before calling explain_instance.')

    def save_explainer(self, path: str):
        """
        Save the explainer.

        Args:
            path (str): Path to save the explainer

        Returns:
            None
        """
        with open(path, 'wb') as fp:
            dill.dump(self.explainer_object, fp)

    def load_explainer(self, path: str):
        """
        Load the explainer

        Args:
            path (str): Path to load the explainer

        Returns:
            None
        """
        with open(path, 'rb') as fp:
            self.explainer_object = dill.load(fp)
