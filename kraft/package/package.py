# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Dominic Lindsay <dcrl94@gmail.com>
#
# Copyright (c) 2020, NEC Laboratories Europe Ltd., NEC Corporation.
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
import os
import shutil
import tempfile 
import tarfile
from enum import Enum, unique
from kraft.package.oci.opencontainers.image.v1 import (
    Index,
    Manifest
)

from kraft.package.oci.opencontainers.digest  import (
    SHA256,
    SHA384,
    SHA512,
    Canonical as default_digest_algorithm,
    digester,
    Algorithm
)

from kraft.package.oci.opencontainers.digest.algorithm import algorithms



from kraft.package.oci.opencontainers.digest import digest
from kraft.logger import logger

OCI_IMAGE_SCHEMA_VERSION = 2

class Artifact:
    def __init__(self, path, image_path):
        """
        Artifact is a base class for wraping some arbitrary content which
        should compressed into a layer and stored as a blob.
        
        :param path to contents.
        :param path contents should be stored in oci-image.
        """
        self._path = path
        self._image_path = image_path

    def create_digest(self, digester):
        """
        returns a digest
        """
        _ = self
        _ = digester
        raise NotImplementedError()

class Image(Artifact):
    # path where image should be stored inside osi-image
    _image_path = '/image/%s'
    def __init__(self, path, architecture, platform):
        """
        Image is an artifact wrapping a path to an image, its architecture and
        platform it was built for.

        :param path to image.
        :param architecture image was built for (e.g. x86_64, ARM64).
        :param platform image was built for (e.g. kvm, xen).
        """
        image_name = os.path.basename(path)
        super().__init__(path, Image._image_path % image_name)
        self._image_name = image_name
        self._architecture = architecture
        self._platform = platform 

class FileSystem(Artifact):
    # path where filesystem should be stored inside osi-image
    _image_path = '/filesystems/%s'
    def __init__(self, path):
        """
        Filesystem used by kernel
        """
        fs_name = os.path.basename(path)
        super().__init__(path, FileSystem._image_path % fs_name)
        pass


"""
Steps for packaing as oci_image tar
*) Create temporary directory (e.g. /tmp/image/)
*) Create oci_imge temp dir (e.g /tmp/image/oci)

*) Create root fs (e.g. /tmp/image/rootfs)

*) Move artefacts to temp root fs (e.g. /tmp/image/rootfs/image/xxxx)
*) tar temp rootfs -> /tmp/image/rootfs.tar.[gz|xz]
*) rootfs_tar_sha = shaXXX /tmp/image.tar.[gz|xz] 
*) move rootfs_tar to oci_image (e.g. /tmp/image/oci/blobs/shaXXX/`rootfs_tar_sha`

*) init config object 
*) config_sha = shaXXX config object
*) write config object to /tmp/image/oci/blobs/shaXXX/`config_sha`

*) Init Manifest object (config sha, layers sha)
*) manifest_sha = shaXXX manfiest object
*) write manifest object to /tmp/image/oci/blobs/shaXXX/`manifest_sha`  

*) init index (manifest sha)
*) write index to manifest /tmp/image/oci/index.json

*) tar oci (e.g. tar czf /tmp/<image_id> /tmp/image/oci)
"""

@unique
class TemporaryDirs(Enum):
    ROOT        = '%s'
    ROOTFS      = '%s/rootfs'
    IMAGE       = '%s/rootfs/image'
    FILESYSTEM  = '%s/rootfs/filesystem'
    ARTIFACTS   = '%s/rootfs/artifacts'
    OCI_IMAGE   = '%s/oci'
    OCI_BLOBS   = '%s/oci/blobs'
    TARS        = '%s/tars' 

    def __init__(self, dirs):
        """
        TemporaryDirs is a wrapper class for managing temporary dirs use for building images.
        """
        if not dirs:
            raise ValueError("Init with create_staging_dirs")
        self._dirs = dirs

    @classmethod
    def create_staging_dirs(cls):
        """
        Creates a temp directory for oci image.
        This method should be called to construct `TemporaryDirs`.
            :return dict of paths to staging directories
        """
        temp_dir = tempfile.mkdtemp()
        temp = {
            'root':         cls.ROOT.value % (temp_dir),
            'rootfs':       cls.ROOTFS.value % (temp_dir),
            'image':        cls.IMAGE.value % (temp_dir),
            'filesystem':   cls.FILESYSTEM.value % (temp_dir),
            'oci_image':    cls.OCI_IMAGE.value % (temp_dir),
            'oci_blobs':    cls.OCI_BLOBS.value % (temp_dir),
            'tars':         cls.TARS.value % (temp_dir) # temp location for tars
            #'artifacts':   '%s/rootfs/artifacts' % (temp_dir),
        }
        ## dont need to check if dir already exists -- tmp file
        for _, dir in temp:
            os.mkdir(dir)
        return TemporaryDirs(temp)

    def delete_staging_dir(self):
        """
        Delete temporary directory.
        """
        os.rmdir(self._dirs['root'])

    def get_path(self, key): 
        if key not in self._dirs:
            raise ValueError("Invalid directory key: %s" % key)
        return self._dirs[key]
    
class Packager:
    def __init__(
        self,
        image="",
        filesystem="",
        uk_conf="",
        artifacts=[],
        digest_algorithm=default_digest_algorithm
    ):
        """
        Package wraps a collection of artifacts and a kernel image into the oci
        image format.

        :param image is the path to kernel image.
        :param filesystem path to filesystem image (e.g. initrd)
        :param uk_conf is a path to the unikernel config file.
        :param artifacts is a list of type `Artifact` encapsulating arbitrary data.
        :param digest_algorithm is the algorithm used default is
            `kraft.package.oci.image.v1.algorithm.Canonical`.
        :param uk_conf is the path to the unikernel configuration file.
        """
        if digest_algorithm not in algorithms:
            raise ValueError("Invalid algorithm selected")
        if not image:
            raise ValueError("Invalid path to kernel image")
        if not uk_conf:
            raise ValueError("Invalid path to image config")
        self._image_path = image
        self._filesystem_path = filesystem 
        self._artifacts = artifacts
        self._uk_config = uk_conf
        self._digester = digest_algorithm.digester()
        self._index = Index()
        self._manifest = Manifest()

    def create_oci_filesystem(self):
        """
        create_oci_filesystem creates the filesystem which should be wrapped up
        by the oci bundle
        """
        staging_dirs = TemporaryDirs.create_staging_dirs()

        image_name = os.path.basename(self._image_path)
        image_path = '%s/%s' %(staging_dirs.get_path('image'), image_name) 
        shutil.copy(self._image_path, image_path)

        if self._filesystem_path:
            fs_name = os.path.basename(self._filesystem_path)
            shutil.copy(self._image_path, '%s/%s'
                        %(staging_dirs.get_path('filesystem'), fs_name))

        ## copy artifacts

        ## tar up rootfs
        tar_rootfs_path = '%s/%s' % (staging_dirs.get_path('tars'), 'rootfs.tar.xz')
        with tarfile.open(tar_rootfs_path, "w") as tar:
            tar.add(image_path)

        ## Create digests
        with open(tar_rootfs_path, 'rb') as f:
            digest.NewDigestFromBytes(Algorithm(SHA256), b'some bytes')

        raise NotImplementedError()

    def configure_index(self):
        self._index.clear()
        self._index.add("schemaVersion", OCI_IMAGE_SCHEMA_VERSION)

    def add_unikraft_config(self, config_path):
        """
        Add a unikraft unikernal config
        """
        ##itterate lines in config and create annotations
        self._uk_config = config_path

    def create_layer(self, artefacts): 
        _ = self
        _ = artefacts
        raise NotImplementedError()

