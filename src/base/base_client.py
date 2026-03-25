from abc import ABC, abstractmethod
from typing import Any
import numpy as np

class BaseClient(ABC):
    """
    Abstract base class for a robot-side client.

    A Client is responsible for:
    1. Getting observation from environment / robot
    2. Sending action back to environment / robot
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_obs(self) -> Any:
        """
        Retrieve observation from robot or environment.

        Returns:
            Observation object (e.g., dict, numpy array, etc.)
        """
        pass

    @abstractmethod
    def post_action(self, action: Any) -> None:
        """
        Send action to robot or environment.

        Args:
            action: Action to execute
        """
        pass

    @abstractmethod
    def infer(self, obs:dict) -> np.ndarray:
        """
        Infer action according to obs.

        Returns:
            action: Action to execute
        """
        pass