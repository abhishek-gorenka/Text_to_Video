# # SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# # SPDX-License-Identifier: Apache-2.0
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# from typing import Any, Tuple

# import numpy as np

# from cosmos1.utils import log


# class ContentSafetyGuardrail:
#     def is_safe(self, **kwargs) -> Tuple[bool, str]:
#         raise NotImplementedError("Child classes must implement the is_safe method")


# class PostprocessingGuardrail:
#     def postprocess(self, frames: np.ndarray) -> np.ndarray:
#         raise NotImplementedError("Child classes must implement the postprocess method")


# class GuardrailRunner:
#     def __init__(
#         self,
#         safety_models: list[ContentSafetyGuardrail] | None = None,
#         generic_block_msg: str = "",
#         generic_safe_msg: str = "",
#         postprocessors: list[PostprocessingGuardrail] | None = None,
#     ):
#         self.safety_models = safety_models
#         self.generic_block_msg = generic_block_msg
#         self.generic_safe_msg = generic_safe_msg if generic_safe_msg else "Prompt is safe"
#         self.postprocessors = postprocessors

#     def run_safety_check(self, input: Any) -> Tuple[bool, str]:
#         """Run the safety check on the input."""
#         if not self.safety_models:
#             log.warning("No safety models found, returning safe")
#             return True, self.generic_safe_msg

#         for guardrail in self.safety_models:
#             guardrail_name = str(guardrail.__class__.__name__).upper()
#             log.debug(f"Running guardrail: {guardrail_name}")
#             safe, message = guardrail.is_safe(input)
#             if not safe:
#                 reasoning = self.generic_block_msg if self.generic_block_msg else f"{guardrail_name}: {message}"
#                 return False, reasoning
#         return True, self.generic_safe_msg

#     def postprocess(self, frames: np.ndarray) -> np.ndarray:
#         """Run the postprocessing on the video frames."""
#         if not self.postprocessors:
#             log.warning("No postprocessors found, returning original frames")
#             return frames

#         for guardrail in self.postprocessors:
#             guardrail_name = str(guardrail.__class__.__name__).upper()
#             log.debug(f"Running guardrail: {guardrail_name}")
#             frames = guardrail.postprocess(frames)
#         return frames


# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Tuple
import numpy as np
from cosmos1.utils import log


class ContentSafetyGuardrail:
    """Abstract base class for content safety guardrails."""

    def is_safe(self, *kwargs) -> Tuple[bool, str]:
        """Check if input content is safe.

        This method must be implemented by child classes.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - A boolean indicating whether the content is safe.
                - A string message describing the result.
        """
        raise NotImplementedError("Child classes must implement the is_safe method")


class PostprocessingGuardrail:
    """Abstract base class for postprocessing guardrails."""

    def postprocess(self, frames: np.ndarray) -> np.ndarray:
        """Postprocess video frames.

        This method must be implemented by child classes.

        Args:
            frames: A numpy array of video frames to process.

        Returns:
            np.ndarray: The processed video frames.
        """
        raise NotImplementedError("Child classes must implement the postprocess method")


class GuardrailRunner:
    """Runner class for managing safety checks and postprocessing."""

    def __init__(
        self,
        safety_models: list[ContentSafetyGuardrail] | None = None,
        generic_block_msg: str = "",
        generic_safe_msg: str = "",
        postprocessors: list[PostprocessingGuardrail] | None = None,
    ):
        """
        Initialize the GuardrailRunner.

        Args:
            safety_models: List of content safety guardrail models.
            generic_block_msg: Generic message to display when input is blocked.
            generic_safe_msg: Generic message to display when input is safe.
            postprocessors: List of postprocessing guardrails.
        """
        self.safety_models = safety_models
        self.generic_block_msg = generic_block_msg
        self.generic_safe_msg = generic_safe_msg if generic_safe_msg else "Prompt is safe"
        self.postprocessors = postprocessors

    def run_safety_check(self, input: Any) -> Tuple[bool, str]:
        """Run the safety check on the input.

        Args:
            input: The input content to check.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - A boolean indicating whether the input is safe.
                - A string message describing the result.
        """
        if not self.safety_models:
            log.warning("No safety models found, returning safe")
            return True, self.generic_safe_msg

        for guardrail in self.safety_models:
            is_safe, guardrail_name = guardrail.is_safe(input)
            if not is_safe:
                msg = self.generic_block_msg if self.generic_block_msg else f"{guardrail_name} blocked input"
                return False, msg

        return True, self.generic_safe_msg

    def postprocess(self, frames: np.ndarray) -> np.ndarray:
        """Postprocess video frames using postprocessing guardrails.

        Args:
            frames: A numpy array of video frames to process.

        Returns:
            np.ndarray: The processed video frames.
        """
        if not self.postprocessors:
            log.debug("No postprocessors found, returning original frames")
            return frames

        for guardrail in self.postprocessors:
            frames = guardrail.postprocess(frames)
            log.debug(f"Postprocessed by {guardrail.__class__.__name__.upper()}")

        return frames
