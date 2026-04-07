"""
Module: 2. Training Pipeline
Author: Forked
Date: 2025-12-31
Purpose: Implements the testcuda module for the 2. Training Pipeline component, supporting training orchestration, evaluation, or experiment control.
"""

import torch

print("CUDA version PyTorch sees:", torch.version.cuda)
print("Is CUDA available:", torch.cuda.is_available())
print("GPU name:", torch.cuda.get_device_name(0))
