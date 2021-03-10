# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Dominic Lindsay <dcrl94@gmail.com>
#
# Copyright (c) 2020, NEC Europe Laboratories GmbH., NEC Corporation.
#                     All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

class ImageConfig:
    def __init__(self, user=None, exposed_ports=[], env=[], entrypoint=[],
                 cmd=[], working_dir=None, volumes=[], labels=[],
                 stop_signal=None):
        """
        ImageConfig defines the execution parameters which should be used as a
        base when running a container from a image.
        """
        self._user = user
        self._exposed_ports = exposed_ports
        self._env = env
        self._entrypoint = entrypoint
        self._cmd = cmd
        self._volumes = volumes
        self._working_dir = working_dir
        self._labels = labels
        self._stop_signal=stop_signal

    @property
    def user(self):
        """
        user defines the username or UID which the process in the container
        should run as.
        """
        return self._user

    @property
    def exposed_ports(self):
        """
        exposed_ports a dict of ports to expose from a container running this
        image.
        """
        self._exposed_ports

    @property
    def env(self):
        """env is a list of environment variables to be used in a container."""
        return self._env

    @property
    def entrypoint(self):
        """
        entrypoint defines a list of arguments to use as the command to execute
        when the container starts.
        """
        return self._entrypoint

    @property
    def cmd(self):
        """
        cmd dict used to define the default arguments to the entrypoint of the
        container.
        """
        return self._cmd


    @property
    def volumes(self):
        """
        volumes is a dict of directories describing where the process is likely
        write data specific to a container instance.
        """
        return self._volumes


    @property
    def working_dir(self):
        """
        working_dir sets the current working directory of the entrypoint
        process in the container.
        """
        return self._working_dir


    @property
    def labels(self):
        """
        labels dict contains arbitrary metadata for the container.
        """
        return self._labels

    @property
    def stop_signal(self):
        """
        stop_signal contains the system call signal that will be sent to the
        container to exit.
        """
        return self._stop_signal

class RootFS:
    def __init__(self, type="", diffIds=[]):
        """RootFS describes layer content addresses"""
        self._type=type
        self._diffIds=diffIds
        # TODO: type check diffIDs is of type `Digest`

    @property
    def type(self):
        """type identifies the 'type' of the rootfs"""
        return self._type

    @property
    def difIds(self):
        """
        diffIds is an array of layer content hashes (DiffIDs), in order from
        bottom-most to top-most.
        """
        return self._diffIds

class History:
    """History describes the history of a layer."""
    def __init__(self, created=None, created_by=None, author=None, comment=None,
                 empty_layer=None):
        self._created = created
        self._created_by = created_by
        self._author = author
        self._comment = comment
        self._empty_layer = empty_layer

    @property
    def created(self):
        """
        created is the combined date and time at which the layer was
        created, formatted as defined by RFC 3339, section 5.6.
        """
        return self._created

    @property
    def created_by(self):
        """createdBy is the command which created the layer."""
        return self._created_by

    @property
    def author(self):
        """Author is the author of the build point."""
        return self._author

    @property
    def comment(self):
        """Comment is a custom message set when creating the layer."""
        return self._comment

    @property
    def empty_layer(self):
        """
        EmptyLayer is used to mark if the history item created a filesystem
        diff.
        """ 
        return self._empty_layer


class Image:
    """
    Image is the JSON structure which describes some basic information about
    the image. This provides the `application/vnd.oci.image.config.v1+json`
    mediatype when marshalled to JSON.
    """
    def __init__(self, created=None, author=None, architecture="", os=None,
                 config=None, rootfs=RootFS(), history=[]):
        self._created = created
        self._author = author 
        self._architecture = architecture
        self._os = os,
        self._config = config
        self._rootfs = rootfs
        self._history = history

    @property
    def created(self):
        """
        Created is the combined date and time at which the image was created,
        formatted as defined by RFC 3339, section 5.6.
        """
        return self._created

    @property
    def author(self):
        """
        Author defines the name and/or email address of the person or entity
        which created and is responsible for maintaining the image.
        """
        return self._author

    @property
    def architecture(self):
        """
        Architecture is the CPU architecture which the binaries in this image
        are built to run on.
        """
        return self._architecture

    @property
    def os(self):
        """
        os is teh name of the operating systems which teh image is built to
        run on.
        """
        return self._os

    @property
    def config(self):
        """
        `config` defines the execution parameters which should be used as a base
        when running a container using the image.
        """
        return self._config

    @property
    def rootfs(self):
        """
        `rootfs` references the layer content addresses used by the image.
        """
        return self._rootfs

    @property
    def history(self):
        """History describes the history of each layer."""
        return self._history
