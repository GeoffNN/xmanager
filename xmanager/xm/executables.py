# Copyright 2021 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Definition of shared executable specifications."""

import abc
import os
import re
from typing import List, NamedTuple, Optional, Union

import attr
from xmanager.xm import core
from xmanager.xm import utils


def _name_from_path(path: str) -> str:
  return re.sub('\\W', '_', os.path.basename(path.rstrip(os.sep)))


class ModuleName(NamedTuple):
  """Name of python module to execute when entering this project."""
  module_name: str


class CommandList(NamedTuple):
  """List of commands to execute when entering this project."""
  commands: List[str]


@attr.s(auto_attribs=True)
class PythonContainer(core.ExecutableSpec):
  """PythonContainer describes a directory containing Python code.

  Attributes:
      entrypoint: The Python module or list of shell commands to run when
        entering this Python project.
      path: Relative or absolute path to the Python project. By default, the
        current directory (`'.'`) is used.
      base_image: Name of the image to initialize a new Docker build stage using
        the instruction `FROM`.
      docker_instructions: List of Docker instructions to apply when building
        the image.

        When you use `docker_instructions`, you are responsible for copying the
        project directory. For example, if you are running with:

          path='/path/to/cifar10'

        You should include these steps in your `docker_instructions`:

          [
            'COPY cifar10/ cifar10',
            'WORKDIR cifar10',
          ]

        If your source code rarely changes, you can make this your first step.
        If you are frequently iterating on the source code, it is best practice
        to place these steps as late as possible in the list to maximize Docker
        layer-caching.
  """

  entrypoint: Union[ModuleName, CommandList]
  path: str = attr.ib(converter=utils.get_absolute_path, default='.')
  base_image: Optional[str] = None
  docker_instructions: Optional[List[str]] = None

  @property
  def name(self) -> str:
    return _name_from_path(self.path)


class BinaryDependency(abc.ABC):
  """Additional resource for `Binary` / `BazelBinary`.

  Implementations can define backend-specific dependencies.
  """


@attr.s(auto_attribs=True)
class Container(core.ExecutableSpec):
  """A prebuilt Docker image.

  The image can be tagged locally or in a remote repository.
  """

  image_path: str

  @property
  def name(self) -> str:
    return _name_from_path(self.image_path)


@attr.s(auto_attribs=True)
class Binary(core.ExecutableSpec):
  """A prebuilt executable program."""

  path: str
  dependencies: List[BinaryDependency] = attr.Factory(list)

  @property
  def name(self) -> str:
    return _name_from_path(self.path)


@attr.s(auto_attribs=True)
class BazelContainer(core.ExecutableSpec):
  """A Bazel target that produces a .tar image.

  Note that for targets based on https://github.com/bazelbuild/rules_docker one
  should append '.tar' to the label to specify a self-contained image.
  """

  label: str

  @property
  def name(self) -> str:
    return _name_from_path(self.label)


@attr.s(auto_attribs=True)
class BazelBinary(core.ExecutableSpec):
  """A Bazel target that produces a self-contained binary.

  Note that for Python targets based on https://github.com/google/subpar one
  should append '.par' to the label to specify a self-contained binary.
  """

  label: str
  dependencies: List[BinaryDependency] = attr.Factory(list)

  @property
  def name(self) -> str:
    return _name_from_path(self.label)
