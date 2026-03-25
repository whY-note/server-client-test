from abc import ABC, abstractmethod
import numpy as np

class BaseServer(ABC):
    """
    Abstract base class for a policy server.

    A Server is responsible for:
    1. Sending observation
    2. Getting action
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def post_obs(self, obs: dict) -> None:
        """
        Send observation to the server.

        Args:
            obs (dict): Observation data (e.g., images, states, etc.)
        """
        pass

    @abstractmethod
    def get_action(self) -> np.ndarray:
        """
        Retrieve action computed by the server.

        Returns:
            np.ndarray: Action output
        """
        pass