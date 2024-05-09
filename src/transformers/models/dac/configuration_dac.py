# coding=utf-8
# Copyright 2023 Meta Platforms, Inc. and affiliates, and the HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" EnCodec model configuration"""


import math
from typing import Optional

import numpy as np

from ...configuration_utils import PretrainedConfig
from ...utils import logging


logger = logging.get_logger(__name__)


from ..deprecated._archive_maps import DAC_PRETRAINED_CONFIG_ARCHIVE_MAP  # noqa: F401, E402


class DacConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of an [`EncodecModel`]. It is used to instantiate a
    Encodec model according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of the
    [facebook/encodec_24khz](https://huggingface.co/facebook/encodec_24khz) architecture.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.

    Args:
        target_bandwidths (`List[float]`, *optional*, defaults to `[1.5, 3.0, 6.0, 12.0, 24.0]`):
            The range of diffent bandwiths the model can encode audio with.
        sampling_rate (`int`, *optional*, defaults to 24000):
            The sampling rate at which the audio waveform should be digitalized expressed in hertz (Hz).
        audio_channels (`int`, *optional*, defaults to 1):
            Number of channels in the audio data. Either 1 for mono or 2 for stereo.
        normalize (`bool`, *optional*, defaults to `False`):
            Whether the audio shall be normalized when passed.
        chunk_length_s (`float`, *optional*):
            If defined the audio is pre-processed into chunks of lengths `chunk_length_s` and then encoded.
        overlap (`float`, *optional*):
            Defines the overlap between each chunk. It is used to compute the `chunk_stride` using the following
            formulae : `int((1.0 - self.overlap) * self.chunk_length)`.
        hidden_size (`int`, *optional*, defaults to 128):
            Intermediate representation dimension.
        num_filters (`int`, *optional*, defaults to 32):
            Number of convolution kernels of first `EncodecConv1d` down sampling layer.
        num_residual_layers (`int`,  *optional*, defaults to 1):
            Number of residual layers.
        upsampling_ratios (`Sequence[int]` , *optional*, defaults to `[8, 5, 4, 2]`):
            Kernel size and stride ratios. The encoder uses downsampling ratios instead of upsampling ratios, hence it
            will use the ratios in the reverse order to the ones specified here that must match the decoder order.
        norm_type (`str`, *optional*, defaults to `"weight_norm"`):
            Normalization method. Should be in `["weight_norm", "time_group_norm"]`
        kernel_size (`int`, *optional*, defaults to 7):
            Kernel size for the initial convolution.
        last_kernel_size (`int`, *optional*, defaults to 7):
            Kernel size for the last convolution layer.
        residual_kernel_size (`int`, *optional*, defaults to 3):
            Kernel size for the residual layers.
        dilation_growth_rate (`int`, *optional*, defaults to 2):
            How much to increase the dilation with each layer.
        use_causal_conv (`bool`, *optional*, defaults to `True`):
            Whether to use fully causal convolution.
        pad_mode (`str`, *optional*, defaults to `"reflect"`):
            Padding mode for the convolutions.
        compress (`int`, *optional*, defaults to 2):
            Reduced dimensionality in residual branches (from Demucs v3).
        num_lstm_layers (`int`, *optional*, defaults to 2):
            Number of LSTM layers at the end of the encoder.
        trim_right_ratio (`float`, *optional*, defaults to 1.0):
            Ratio for trimming at the right of the transposed convolution under the `use_causal_conv = True` setup. If
            equal to 1.0, it means that all the trimming is done at the right.
        codebook_size (`int`, *optional*, defaults to 1024):
            Number of discret codes that make up VQVAE.
        codebook_dim (`int`, *optional*):
            Dimension of the codebook vectors. If not defined, uses `hidden_size`.
        use_conv_shortcut (`bool`, *optional*, defaults to `True`):
            Whether to use a convolutional layer as the 'skip' connection in the `EncodecResnetBlock` block. If False,
            an identity function will be used, giving a generic residual connection.

    Example:

    ```python
    >>> from transformers import EncodecModel, EncodecConfig

    >>> # Initializing a "facebook/encodec_24khz" style configuration
    >>> configuration = EncodecConfig()

    >>> # Initializing a model (with random weights) from the "facebook/encodec_24khz" style configuration
    >>> model = EncodecModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "dac"

    def __init__(
        self,
        num_codebooks: int = 9,
        model_bitrate: int = 8,  # kbps
        codebook_size: int = 1024,
        latent_dim: int = 1024,
        frame_rate: int = 86,
        sampling_rate: int = 44100,
        **kwargs,
    ):
        self.codebook_size = codebook_size
        self.model_bitrate = model_bitrate
        self.latent_dim = latent_dim
        self.num_codebooks = num_codebooks
        self.frame_rate = frame_rate
        self.sampling_rate = sampling_rate

        super().__init__(**kwargs)

    # This is a property because you might want to change the chunk_length_s on the fly
    @property
    def chunk_length(self) -> Optional[int]:
        if self.chunk_length_s is None:
            return None
        else:
            return int(self.chunk_length_s * self.sampling_rate)

    # This is a property because you might want to change the chunk_length_s on the fly
    @property
    def chunk_stride(self) -> Optional[int]:
        if self.chunk_length_s is None or self.overlap is None:
            return None
        else:
            return max(1, int((1.0 - self.overlap) * self.chunk_length))

    @property
    def frame_rate(self) -> int:
        hop_length = np.prod(self.upsampling_ratios)
        return math.ceil(self.sampling_rate / hop_length)

    @property
    def num_quantizers(self) -> int:
        return int(1000 * self.target_bandwidths[-1] // (self.frame_rate * 10))
