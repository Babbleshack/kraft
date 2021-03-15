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
from kraft.package.oci.opencontainers.digest import Digest
from kraft.package.oci.opencontainers.image.v1 import (
    Index,
    Manifest,
)
from kraft.package.oci.opencontainers.image.v1.config import (
    ImageConfig,
    Image,
    RootFS,
    History
)
from kraft.package.oci.opencontainers.digest  import (
    Canonical as default_digest_algorithm,
)
from kraft.package.oci.opencontainers.image.specs import Version
from kraft.package.oci.opencontainers.digest.exceptions import ErrDigestInvalidFormat
from kraft.package.oci.opencontainers.digest.algorithm import algorithms
from kraft.error import KraftError
#from kraft.logger import logger

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

class ImageWrapper(Artifact):
    # path where image should be stored inside osi-image
    _image_path = '/image/%s'
    def __init__(self, path, architecture, platform):
        """
        ImageWrapper is an artifact wrapping a path to an image, its architecture and
        platform it was built for.

        :param path to image.
        :param architecture image was built for (e.g. x86_64, ARM64).
        :param platform image was built for (e.g. kvm, xen).
        """
        image_name = os.path.basename(path)
        super().__init__(path, Image._image_path % image_name)
        self._image = image_name
        self._architecture = architecture
        self._platform = platform 

    @property
    def image(self):
        return self._image

    @property
    def architecture(self):
        return self._architecture
    
    @property
    def platform(self):
        return self._platform


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
[x] Create temporary directory (e.g. /tmp/image/)
[x] Create oci_imge temp dir (e.g /tmp/image/oci)

[x] Create rootfs (e.g. /tmp/image/rootfs)

[x] Move artefacts to temp root fs (e.g. /tmp/image/rootfs/image/xxxx)
[x] tar temp rootfs -> /tmp/image/rootfs.tar.[gz|xz]
[x] rootfs_tar_digest = shaXXX /tmp/image.tar.[gz|xz] 
[x] move rootfs_tar to oci_image (e.g. /tmp/image/oci/blobs/shaXXX/`rootfs_tar_digest.encoded`

[x] init config object 
[x] add image config attribs
[] config_digest = shaXXX config object
[] write config object to /tmp/image/oci/blobs/shaXXX/`config_digest.encoded`

[x] Init Manifest object (config sha, layers sha)
[] manifest_digest = shaXXX manfiest object
[] write manifest object to /tmp/image/oci/blobs/shaXXX/`manifest_digest.encoded`  

[x] init index (manifest sha)
[] write index to manifest /tmp/image/oci/index.json

[] tar oci (e.g. tar czf /tmp/<image_id> /tmp/image/oci)
"""

class TemporaryDirs:
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
        TemporaryDirs is a wrapper class managing temporary dirs used for building images.
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
            'root':         cls.ROOT % (temp_dir),
            'rootfs':       cls.ROOTFS % (temp_dir),
            'image':        cls.IMAGE % (temp_dir),
            'filesystem':   cls.FILESYSTEM % (temp_dir),
            'oci_image':    cls.OCI_IMAGE % (temp_dir),
            'oci_blobs':    cls.OCI_BLOBS % (temp_dir),
            'tars':         cls.TARS % (temp_dir) # temp location for tars
            #'artifacts':   '%s/rootfs/artifacts' % (temp_dir),
        }
        ## dont need to check if dir already exists -- tmp file
        for key, dir in temp.items():
            #skip root this is the temo dir
            if key == 'root':
                continue
            os.mkdir(dir)
        return TemporaryDirs(temp)

    def delete_staging_dir(self):
        """
        Delete temporary directory.
        """
        os.rmdir(self._dirs['root'])

    def get_path(self, key): 
        """
        Get a path managed by TemporaryDirs
        :return path
        :raise ValueError if invalid key
        """
        if key not in self._dirs:
            raise ValueError("Invalid directory key: %s" % key)
        return self._dirs[key]

## TODO: figure out how to pass class/static var as default __init__ param
HASH_BUFF_SIZE = 1024 * 64 #64k
class Packager:
    def __init__(
        self,
        image=ImageWrapper(path=None, architecture=None, platform=None),
        filesystem="",
        uk_conf="",
        artifacts=[],
        digest_algorithm=default_digest_algorithm,
        hash_buffer_size=HASH_BUFF_SIZE
    ):
        """
        Package wraps a collection of artifacts and a kernel image into the oci
        image format.

        :param image is the path to kernel image.
        :param filesystem path to filesystem image (e.g. initrd)
        :param uk_conf is a path to the unikernel config file.
        :param artifacts is a list of type `Artifact` encapsulating arbitrary data.
        :param digest_algorithm is the algorithm used.
            valid options are one of `kraft.package.oci.image.v1.algorithm.algorithms` 
            (e.g. "sha256", "sha384", "sha512")
        :param uk_conf is the path to the unikernel configuration file.
        :param optional, set hash buffer size.
        """
        if not image:
            raise KraftError(ValueError("Invalid path to kernel image"))
        if not uk_conf:
            raise KraftError(ValueError("Invalid path to image config"))
        if digest_algorithm not in algorithms:
            raise KraftError(ValueError("Invalid algorithm selected"))
        self._image = image
        self._filesystem_path = filesystem 
        self._artifacts = artifacts
        self._uk_config = uk_conf
        self._digester = digest_algorithm.digester()
        self._index = None
        self._manifest = None
        self._image_config = None
        self._hash_buff_size = hash_buffer_size

    def create_oci_filesystem(self):
        """
        create_oci_filesystem creates OCI Image rootfs, tars it and creates a digest.
        :return dict{'path': <path to tar>, 'digest': <digest over tared contents>}.
        """
        staging_dirs = TemporaryDirs.create_staging_dirs()
        image_name = os.path.basename(self._image.path)
        image_path = '%s/%s' %(staging_dirs.get_path('image'), image_name) 
        shutil.copy2(self._image.path, image_path)
        if self._filesystem_path:
            fs_name = os.path.basename(self._filesystem_path)
            shutil.copy(self._image.path, '%s/%s'
                        %(staging_dirs.get_path('filesystem'), fs_name))
        ## copy artifacts/filesystem

        ## tar up rootfs
        tar_rootfs_path = '%s/%s' % (staging_dirs.get_path('tars'), 'rootfs.tar.gz')
        with tarfile.open(tar_rootfs_path, "w:gz") as tar:
            tar.add(staging_dirs.get_path('rootfs'), arcname='/rootfs')
        tar_digest = {
            'path': tar_rootfs_path,
            'digest': None
        }
        ## Create digests
        with open(tar_rootfs_path, 'rb') as f:
            data = f.read(self._hash_buff_size)
            while data:
                self._digester.hash.update(data)
                data = f.read(self._hash_buff_size)
            tar_digest['digest'] = self._digester.digest() 
        try:
            tar_digest['digest'].validate()
        except ErrDigestInvalidFormat as e:
            raise KraftError("Invalid rootfs digest: %s" % e)
        return tar_digest

    def create_oci_config(self, rootfs_digest=Digest()):
        if not rootfs_digest.validate():
            raise KraftError("Malformed digest value for rootfs")
        self._image_config = Image(
            arch=self._image.architecture,
            rootfs=rootfs_digest,
            imageOS="linux"
        )
        return self._image_config

    def create_oci_manifest(self,
                            config_digest=Digest(),
                            layer_digests=[]):
        self._manifest = Manifest(
            manifestConfig=config_digest,
            layers=layer_digests,
            schemaVersion = Version
        )
        return self._manifest

    def configure_index(self, manifest_digests=list(Digest())):
        for manifest in manifest_digests:
            if not manifest.validate():
                raise KraftError("Malformed manifest digest")
        self._index = Index(
            manifests=manifest_digests,
            schemaVersion = Version
        )
        return self._index
        
