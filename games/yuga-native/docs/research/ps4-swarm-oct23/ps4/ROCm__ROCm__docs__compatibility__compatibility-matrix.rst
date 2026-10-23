:selector-toc2: Installation environment
:selector-toc2-icon: fa-solid fa-computer

.. _compat-matrix:

****************************************
ROCm |ROCM_VERSION| compatibility matrix
****************************************

To plan your ROCm |ROCM_VERSION| installation, use the following selector to
view ROCm compatibility and system requirements information for your AMD
hardware configuration and system environment. For installation instructions,
see :doc:`/install/rocm`.

.. selector:: Device family
   :key: fam

   .. selector-option:: AMD Instinct™
      :value: instinct
      :width: 4
      :toc-label: AMD Instinct

   .. selector-option:: AMD Radeon™
      :value: radeon
      :width: 4
      :toc-label: AMD Radeon

   .. selector-option:: AMD Ryzen™
      :value: ryzen
      :width: 4
      :toc-label: AMD Ryzen

.. datatemplate:yaml:: /data/gpus.yaml
   :template: gpu-selector.rst.jinja

.. datatemplate:yaml:: /data/gpus.yaml
   :template: os-selector.rst.jinja

----

.. _system-requirements:

System requirements and information
===================================

ROCm depends on a coordinated stack of compatible firmware, driver, and user
space components. Maintaining version alignment between these layers ensures
expected GPU operation and performance, especially for AMD data center
products. This table lists GPU details followed by supported operating systems,
kernel driver, and firmware versions.

.. datatemplate:yaml:: /data/gpus.yaml
   :template: system-instinct.rst.jinja

.. datatemplate:yaml:: /data/gpus.yaml
   :template: system-radeon.rst.jinja

.. datatemplate:yaml:: /data/gpus.yaml
   :template: system-ryzen.rst.jinja

For hardware specifications, see :ref:`gpu-specs`.

----

.. datatemplate:yaml:: /data/virtualization-support.yaml
   :template: virtualization-instinct.rst.jinja

.. datatemplate:yaml:: /data/virtualization-support.yaml
   :template: virtualization-radeon.rst.jinja

----

.. datatemplate:yaml:: /data/partitioning-support.yaml
   :template: partitioning-support.rst.jinja

----

ROCm Core SDK components
========================

The following table lists core components included in the ROCm |ROCM_VERSION|
release. Expect future releases in this stream to expand the list of
components.

.. datatemplate:yaml:: /data/components-current.yaml
   :template: core-sdk-components-linux.rst.jinja

.. datatemplate:yaml:: /data/components-current.yaml
   :template: core-sdk-components-windows.rst.jinja

----

.. _rocm-compat-frameworks:

.. _rocm-compat-python:

.. _rocm-compat-pytorch:

AI ecosystem compatibility
==========================

ROCm |ROCM_VERSION| provides optimized support for popular deep learning
frameworks and AI inference engines. The following table lists supported
frameworks and libraries, their validated versions, and compatible Python
versions.

.. include:: ./include/ai-ecosystem.rst

