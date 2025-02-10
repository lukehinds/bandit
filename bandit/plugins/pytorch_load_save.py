# Copyright (c) 2024 Stacklok, Inc.
#
# SPDX-License-Identifier: Apache-2.0
r"""
==========================================
B614: Test for unsafe PyTorch load or save
==========================================

This plugin checks for the use of `torch.load` and `torch.save`. Using
`torch.load` with untrusted data can lead to arbitrary code execution, and
improper use of `torch.save` might expose sensitive data or lead to data
corruption. A safe alternative is to use `torch.load` with the `safetensors`
library from huggingface, which provides a safe deserialization mechanism. A
second option is to use the `weights_only` argument for `torch.load` where
only tensor data is extracted, and no arbitrary Python objects (like custom
layers, optimizers or hooks) are deserialized. With `weights_only=True`, PyTorch
enforces a strict type check, ensuring that only torch.Tensor objects are loaded.
:Example:

.. code-block:: none

        >> Issue: Use of unsafe PyTorch load or save
        Severity: Medium   Confidence: High
        CWE: CWE-94 (https://cwe.mitre.org/data/definitions/94.html)
        Location: examples/pytorch_load_save.py:8
        7    loaded_model.load_state_dict(torch.load('model_weights.pth'))
        8    another_model.load_state_dict(torch.load('model_weights.pth',
                map_location='cpu'))
        9
        10   print("Model loaded successfully!")

.. seealso::

     - https://cwe.mitre.org/data/definitions/94.html
     - https://pytorch.org/docs/stable/generated/torch.load.html#torch.load
     - https://github.com/huggingface/safetensors

.. versionadded:: 1.7.10

"""
import bandit
from bandit.core import issue
from bandit.core import test_properties as test


@test.checks("Call")
@test.test_id("B614")
def pytorch_load_save(context):
    """
    This plugin checks for the use of `torch.load` and `torch.save`. Using
    `torch.load` with untrusted data can lead to arbitrary code execution,
    and improper use of `torch.save` might expose sensitive data or lead
    to data corruption.
    """
    imported = context.is_module_imported_exact("torch")
    qualname = context.call_function_name_qual
    if not imported and isinstance(qualname, str):
        return

    qualname_list = qualname.split(".")
    func = qualname_list[-1]
    if all(
        [
            "torch" in qualname_list,
            func == "load",
        ]
    ):
        # For torch.load, check if weights_only=True is specified
        weights_only = context.get_call_arg_value("weights_only")
        if weights_only == "True" or weights_only is True:
            return

        return bandit.Issue(
            severity=bandit.MEDIUM,
            confidence=bandit.HIGH,
            text="Use of unsafe PyTorch load or save",
            cwe=issue.Cwe.DESERIALIZATION_OF_UNTRUSTED_DATA,
            lineno=context.get_lineno_for_call_arg("load"),
        )
