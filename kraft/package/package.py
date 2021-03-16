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
import kraft.package.oci.opencontainers.image.v1 as Imagev1
from kraft.package.oci.opencontainers.image.v1 import (
    Index,
    Manifest,
    Descriptor,
    RootFS
)
import kraft.package.oci.opencontainers.image.v1.mediatype as MediaType
from kraft.package.oci.opencontainers.image.v1.config import Image
from kraft.package.oci.opencontainers.digest  import Canonical as default_digest_algorithm
from kraft.package.oci.opencontainers.image.specs import (
    Versioned,
    Version
)
from kraft.package.oci.opencontainers.digest.algorithm import algorithms
from kraft.package.oci.opencontainers.digest.exceptions import (
    ErrDigestUnsupported,
    ErrDigestInvalidLength,
    ErrDigestInvalidFormat
)
from kraft.error import KraftError
#from kraft.logger import logger

OCI_IMAGE_SCHEMA_VERSION = 2

class ArtifactWrapper:
    def __init__(self, path):
        """
        Artifact is a base class for wraping some arbitrary content which
        should compressed into a layer and stored as a blob.
        
        :param path to contents.
        :param path contents should be stored in oci-image.
        """
        self._path = path

    @property
    def path(self):
        return self._path
        
    def validate(self):
        """
        validate artifact exists
        """
        return os.path.isfile(self.path)

class ImageWrapper(ArtifactWrapper):
    # path where image should be stored inside osi-image
    _image_path = '/image/%s'
    def __init__(self, path="", architecture="", platform="", uk_conf=""):
        """
        ImageWrapper is an artifact wrapping a path to an image, its architecture and
        platform it was built for.

        :param path to image.
        :param architecture image was built for (e.g. x86_64, ARM64).
        :param platform image was built for (e.g. kvm, xen).
        :param uk_conf path to configuration file for building uk image
        """
        if not path:
            raise KraftError(ValueError("Invalid path to kernel image."))
        if not architecture:
            raise KraftError(ValueError("Invalid architecture."))
        if not platform:
            raise KraftError(ValueError("Invalid platform."))
        if not uk_conf:
            raise KraftError(ValueError("Invalid path to unikraft config file."))
        super().__init__(path)
        #image_name = os.path.basename(path)
        self._image_name = os.path.basename(path)
        self._architecture = architecture
        self._platform = platform 
        self._conf = uk_conf

    @property
    def image_name(self):
        return self._image_name

    @property
    def architecture(self):
        return self._architecture
    
    @property
    def platform(self):
        return self._platform

    @property
    def config(self):
        return self._conf


class FilesystemWrapper(ArtifactWrapper):
    # path where filesystem should be stored inside osi-image
    _image_path = '/filesystems/%s'
    def __init__(self, path):
        """
        Filesystem used by kernel
        """
        _ = self
        super().__init__(path)

    @property
    def name(self):
        """
        return filename of Filesystem
        """
        return os.path.basename(self._path)

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
    ROOT            = ('root', '%s')
    ROOTFS          = ('rootfs', '%s/rootfs')
    IMAGE           = ('image', '%s/rootfs/image')
    FILESYSTEM      = ('filesystem', '%s/rootfs/filesystem')
    ARTIFACTS       = ('artifacts', '%s/rootfs/artifacts')
    OCI_IMAGE       = ('oci_image', '%s/oci')
    OCI_BLOBS       = ('oci_blobs', '%s/oci/blobs')
    OCI_BLOBS_SHA   = ('oci_blobs_sha', '%s/oci/blobs/%s')
    OCI_INDEX       = ('oci_index', '%s/oci/index.json')
    TARS            = ('tars', '%s/tars' )
    SCRATCH         = ('scratch', '%s/scratch')

    def __init__(self, dirs):
        """
        TemporaryDirs is a wrapper class managing temporary dirs used for building images.
        """
        if not dirs:
            raise ValueError("Init with create_staging_dirs")
        self._dirs = dirs

    @classmethod
    def create(cls, sha):
        # TODO check in valid algorithms
        if not sha:
            raise ValueError("sha must be set to legal sha algorithm")
        """
        Creates a temp directory for oci image.
        This method should be called to construct `TemporaryDirs`.
            :return dict of paths to staging directories
        """
        temp_dir = tempfile.mkdtemp()
        temp = {
            cls.ROOT[0]:            cls.ROOT[1] % (temp_dir),
            cls.ROOTFS[0]:          cls.ROOTFS[1] % (temp_dir),
            cls.IMAGE[0]:           cls.IMAGE[1] % (temp_dir),
            cls.FILESYSTEM[0]:      cls.FILESYSTEM[1] % (temp_dir),
            cls.OCI_IMAGE[0]:       cls.OCI_IMAGE[1] % (temp_dir),
            cls.OCI_BLOBS[0]:       cls.OCI_BLOBS[1] % (temp_dir),
            cls.OCI_BLOBS_SHA[0]:   cls.OCI_BLOBS_SHA[1] %(temp_dir, sha),
            cls.OCI_INDEX[0]:       cls.OCI_INDEX[1] % (temp_dir),
            cls.TARS[0]:            cls.TARS[1] % (temp_dir), # temp location for tars
            cls.SCRATCH[0]:         cls.SCRATCH[1] % (temp_dir)
            #'artifacts':   '%s/rootfs/artifacts' % (temp_dir),
        }
        skip = [cls.ROOT[0], cls.OCI_INDEX[0]]
        ## dont need to check if dir already exists -- tmp file
        for key, dir in temp.items():
            #skip some dirs
            if key in  skip:
                continue
            os.mkdir(dir)
        return TemporaryDirs(temp)

    def delete(self):
        """
        Delete temporary directory.
        """
        shutil.rmtree(self._dirs[self.ROOT[0]])

    def get_path(self, key): 
        """
        Get a path managed by TemporaryDirs
        :return path
        :raise ValueError if invalid key
        """
        if key not in self._dirs:
            raise ValueError("Invalid directory key: %s" % key)
        return self._dirs[key]

    def get_config_path(self, config_hash):
        path = self._dirs[self.__class__.OCI_BLOBS_SHA[0]]
        return "%s/%s" %(path, config_hash)

    def get_blob_path(self, digest_hash):
        return "%s/%ss" % (self._dirs['oci_blobs_sha'], digest_hash)

def _validate(manifest):
    """
    _validate some oci struct
    :raise KraftError if struct is invalid
    """
    try:
        manifest.validate()
    except ErrDigestUnsupported as e:
        raise KraftError("Malformed rootfs digest: %s" % e)
    except ErrDigestInvalidLength as e:
        raise KraftError("Malformed rootfs digest: %s" % e)
    except ErrDigestInvalidFormat as e:
        raise KraftError("Malformed rootfs digest: %s" % e)

class DigestWrapper:
    def __init__(self, digest, path, media_type):
        """
        DigestWrapper wraps a digest and a path to the file referenced by the
        digest.
        :param digest to wrap.
        :param path to file digest references.
        :param media_type is oci media type
        """
        self._digest = digest
        self._path = path
        self._media_type = media_type

    @property
    def digest(self):
        """
        digest of the artifact
        """
        return self._digest

    @property
    def path(self):
        """
        path to artifact
        """
        return self._path

    @property
    def media_type(self):
        """
        oci mediatype of the artifact the digest references
        """
        return self._media_type

    @property
    def size(self):
        """
        size of the artifact
        :raise KraftError if file cannot be accessed.
        """
        if not os.path.isfile(self._path):
            raise KraftError("Error can not access %s" % self._path)
        return os.path.getsize(self._path)

    @property
    def descriptor(self):
        """
        return a descriptor of the wrapped digest
        """
        return Descriptor(
            digest = self.digest,
            mediatype = self.media_type,
            size = self.size)

## TODO: figure out how to pass class/static var as default __init__ param
HASH_BUFF_SIZE = 1024 * 64 #64k
## TODO: refactor duplicate code
class Packager:
    def __init__(
        self,
        #image=ImageWrapper(path=None, architecture=None, platform=None, uk_conf=None),
        image: ImageWrapper = None,
        filesystem: FilesystemWrapper = None,
        artifacts: list[ArtifactWrapper] = None,
        digest_algorithm=default_digest_algorithm,
        hash_buffer_size=HASH_BUFF_SIZE,
        temporary_dirs: TemporaryDirs = None
    ):
        """
        Package wraps a collection of artifacts and a kernel image into the oci
        image format.

        :param image is a ImageWrapper object 
        :param filesystem path to filesystem image (e.g. initrd)
        :param artifacts is a list of type `Artifact` encapsulating arbitrary data.
        :param digest_algorithm is the algorithm used.
            valid options are one of `kraft.package.oci.image.v1.algorithm.algorithms` 
            (e.g. "sha256", "sha384", "sha512")
        :param uk_conf is the path to the unikernel configuration file.
        :param optional, set hash buffer size.
        """
        if not image:
            raise KraftError(ValueError("image must be set"))
        if digest_algorithm not in algorithms:
            raise KraftError(ValueError("Invalid algorithm selected"))
        if not temporary_dirs:
            temporary_dirs = TemporaryDirs.create(digest_algorithm)
        self._image = image
        self._filesystem = filesystem 
        self._artifacts = artifacts
        self._digest_algo = digest_algorithm
        self._hash_buff_size = hash_buffer_size
        self._index = None
        self._manifest = None
        self._image_config = None
        self._filesystem_tar_digest = None
        self._temporary_dirs = temporary_dirs

    def create_oci_filesystem(self) -> DigestWrapper:
        """
        create_oci_filesystem creates OCI Image rootfs, tars it and creates a digest.
        :return tar_rootfs_path to rootfs
            digest string of rootfs tar
            staging_directories temp fs storing artifacts
        """
        digester = self._digest_algo.digester()
        staging_dirs = TemporaryDirs.create(digester.digest().algorithm.value)
        image_name = os.path.basename(self._image.path)
        image_path = '%s/%s' %(staging_dirs.get_path('image'), image_name) 
        shutil.copy2(self._image.path, image_path)
        if self._filesystem:
            fs_name = os.path.basename(self._filesystem.path)
            shutil.copy(self._image.path, '%s/%s'
                        %(staging_dirs.get_path('filesystem'), fs_name))
        ## copy artifacts/filesystem

        ## tar up rootfs
        tar_rootfs_path = '%s/%s' % (staging_dirs.get_path('tars'), 'rootfs.tar.gz')
        with tarfile.open(tar_rootfs_path, "w:gz") as tar:
            tar.add(staging_dirs.get_path('rootfs'), arcname='/rootfs')
        digest = None
        ## Create digests
        with open(tar_rootfs_path, 'rb') as f:
            data = f.read(self._hash_buff_size)
            while data:
                digester.hash.update(data)
                data = f.read(self._hash_buff_size)
            digest = digester.digest()
        try:
            _validate(digest)
        except KraftError as e:
            raise e
        self._filesystem_tar_digest = digest
        #move to oci dir
        digest_path = "%s/%s" %(self._temporary_dirs.get_path('oci_blobs_sha'), digest.encoded())
        shutil.move(tar_rootfs_path, digest_path)
        return DigestWrapper(
            digest = digest,
            path = digest_path,
            media_type = MediaType.MediaTypeImageLayerGzip
        )

    def create_oci_config(self, 
                          rootfs_digest: DigestWrapper) -> DigestWrapper:
        try:
            _validate(rootfs_digest.digest)
        except KraftError as e:
            raise e
        rootfs_d = {
            "type": "layers",
            "diff_ids": [rootfs_digest.digest]
        }
        #rootfs = RootFS(rootfs_type="layers", diff_ids=[rootfs_digest.digest])
        image_config = Image(
            arch=self._image.architecture,
            imageOS="linux",
            rootfs=rootfs_d
        )
        try:
            _validate(image_config)
        except KraftError as e:
            raise e
        self._image_config = image_config
        # write to scracth, get digest move to oci path
        scratch_file = "%s/config.json" %(self._temporary_dirs.get_path('scratch'))
        with open(scratch_file, "w") as f:
            f.write(image_config.to_json())
        digester = self._digest_algo.digester()
        digest = ""
        with open(scratch_file, 'rb') as f:
            data = f.read(self._hash_buff_size)
            while data:
                digester.hash.update(data)
                data = f.read(self._hash_buff_size)
            digest = digester.digest()
        try:
            _validate(digest)
        except KraftError as e:
            raise e
        digest_path = "%s/%s" %(self._temporary_dirs.get_path('oci_blobs_sha'), digest.encoded())
        p = shutil.move(scratch_file, digest_path)
        try:
            _validate(digest)
        except KraftError as e:
            raise e
        return DigestWrapper(
            digest = digest,
            path = digest_path,
            media_type = MediaType.MediaTypeImageConfig
        )

    def create_oci_manifest(self,
                            config_digest: DigestWrapper,
                            layer_digests: list[DigestWrapper]) -> DigestWrapper:
        conf_descriptor = config_digest.descriptor
        layer_descriptors = [dw.descriptor for dw in layer_digests]
        layers_d = [dw.to_dict() for dw in layer_descriptors]
        manifest = Imagev1.Manifest(
            manifestConfig=conf_descriptor.to_dict(),
            layers=layers_d,
            schemaVersion = Versioned(2)
        )
        # write 
        scratch_file = "%s/manifest.json" %(self._temporary_dirs.get_path('scratch'))
        #print("versioned %s"  % Versioned(2))
        #print("manifest %s"  % manifest)
        #print("manifest vars %s"  % vars(manifest))
        #print("manifest dict %s" % manifest.to_dict())
        #print("manifest json %s" % manifest.to_json())
        with open(scratch_file, "w") as f:
            f.write(manifest.to_json())
        digester = self._digest_algo.digester()
        digest = ""
        with open(scratch_file, 'rb') as f:
            data = f.read(self._hash_buff_size)
            while data:
                digester.hash.update(data)
                data = f.read(self._hash_buff_size)
            digest = digester.digest()
        try:
            _validate(digest)
        except KraftError as e:
            raise e
        digest_path = self._temporary_dirs.get_blob_path(digest.encoded())
        shutil.move(scratch_file, digest_path)
        return DigestWrapper(
            digest = digest,
            path = digest_path,
            media_type = MediaType.MediaTypeImageManifest
        )

    def create_index(self, manifest_digests: list[DigestWrapper]) -> str:
        manifest_descriptors = [dw.descriptor.to_dict() for dw in manifest_digests]
        index = Index(
            manifests=manifest_descriptors,
            schemaVersion=2
        )
        try:
            _validate(index)
        except KraftError as e:
            raise e
        index_path = self._temporary_dirs.get_path(self._temporary_dirs.OCI_INDEX[0])
        with open(index_path, "w") as f:
            f.write(index.to_json())
        return index_path
