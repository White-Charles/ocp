from contextlib import contextmanager

import torch
from torch_geometric.data import Batch, Data

from .config import NormalizerTargetConfig


def normalizer_transform(config: dict[str, NormalizerTargetConfig]):
    def transform(data: Data):
        nonlocal config
        for target, target_config in config.items():
            if target not in data:
                raise ValueError(f"Target {target} not found in data.")

            data[target] = (
                torch.tensor(data[target])
                if not isinstance(data[target], torch.Tensor)
                else data[target]
            )
            data[target] = (
                data[target] - target_config.mean
            ) / target_config.std
            data[f"{target}_norm_mean"] = torch.full_like(
                data[target], target_config.mean
            )
            data[f"{target}_norm_std"] = torch.full_like(
                data[target], target_config.std
            )

        return data

    return transform


def denormalize_batch(
    batch_list: list[Batch],
    additional_tensors: dict[str, torch.Tensor] | None = None,
):
    if additional_tensors is None:
        additional_tensors = {}

    keys: set[str] = set([k for batch in batch_list for k in batch.keys])  # type: ignore

    # find all keys that have a norm_mean and norm_std
    norm_keys: set[str] = {
        key.replace("_norm_mean", "")
        for key in keys
        if key.endswith("_norm_mean")
    } & {
        key.replace("_norm_std", "")
        for key in keys
        if key.endswith("_norm_std")
    }

    for key in norm_keys:
        for batch in batch_list:
            mean = getattr(batch, f"{key}_norm_mean")
            std = getattr(batch, f"{key}_norm_std")
            value = getattr(batch, key)

            value = (value * std) + mean
            setattr(batch, key, value)

            additional_value = additional_tensors.pop(key, None)
            if additional_value is not None:
                additional_tensors[key] = (additional_value * std) + mean

    return batch_list, additional_tensors


@contextmanager
def denormalize_context(
    batch_list: list[Batch],
    additional_tensors: dict[str, torch.Tensor] | None = None,
):
    if additional_tensors is None:
        additional_tensors = {}

    keys: set[str] = set([k for batch in batch_list for k in batch.keys])  # type: ignore

    # find all keys that have a norm_mean and norm_std
    norm_keys: set[str] = {
        key.replace("_norm_mean", "")
        for key in keys
        if key.endswith("_norm_mean")
    } & {
        key.replace("_norm_std", "")
        for key in keys
        if key.endswith("_norm_std")
    }

    for key in norm_keys:
        for batch in batch_list:
            mean = getattr(batch, f"{key}_norm_mean")
            std = getattr(batch, f"{key}_norm_std")
            value = getattr(batch, key)

            value = (value * std) + mean
            setattr(batch, key, value)

            additional_value = additional_tensors.pop(key, None)
            if additional_value is not None:
                additional_tensors[key] = (additional_value * std) + mean

    yield batch_list, additional_tensors

    for key in norm_keys:
        for batch in batch_list:
            mean = getattr(batch, f"{key}_norm_mean")
            std = getattr(batch, f"{key}_norm_std")
            value = getattr(batch, key)

            value = (value - mean) / std
            setattr(batch, key, value)

            additional_value = additional_tensors.pop(key, None)
            if additional_value is not None:
                additional_tensors[key] = (additional_value - mean) / std


def denormalize_tensors(
    batch_list: list[Batch],
    key: str,
    tensors: tuple[torch.Tensor, ...],
    mask: torch.Tensor | None = None,
) -> tuple[torch.Tensor, ...]:
    assert len(batch_list) == 1, "Only one batch is supported."
    batch = batch_list[0]

    mean = getattr(batch, f"{key}_norm_mean")
    std = getattr(batch, f"{key}_norm_std")
    if mask is not None:
        mean = mean[mask]
        std = std[mask]

    return tuple((value * std) + mean for value in tensors)