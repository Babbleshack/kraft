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
from typing import (
    Tuple,
    List
)
from opencontainers.digest import Algorithm 
import opencontainers.image.v1 as Imagev1
from opencontainers.image.v1 import (
    Index,
    Descriptor,
)
import opencontainers.image.v1.mediatype as MediaType
from opencontainers.image.v1.config import Image
from opencontainers.digest  import Canonical as default_digest_algorithm
from opencontainers.image.specs import Versioned 
from opencontainers.digest.algorithm import algorithms
from opencontainers.digest.exceptions import (
    ErrDigestUnsupported,
    ErrDigestInvalidLength,
    ErrDigestInvalidFormat
)
from opencontainers.image.v1.layout import ImageLayout
from kraft.error import KraftError



## TODO: get schema version from opencontainers package
OCI_IMAGE_SCHEMA_VERSION = 2
## TODO: figure out how to pass class/static var as default __init__ param
HASH_BUFF_SIZE = 1024 * 64 #64k
## TODO: Add zstd support
#ZSTD="zstd"
compression_algorithms = {"tar": "w", "gzip": "w:gz"}

#default compression algorithm
DEFAULT_COMPRESSION = "gzip"

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
    def __init__(self, path):
        """
        Filesystem used by kernel
        """
        _ = self
        super().__init__(path)

class TemporaryDirs:
    ROOT                        = ('root', '%s')
    ROOTFS                      = ('rootfs', '%s/rootfs')
    IMAGE                       = ('image', '%s/rootfs/image')
    FILESYSTEM                  = ('filesystem', '%s/rootfs/filesystem')
    ARTIFACTS                   = ('artifacts', '%s/rootfs/artifacts')
    OCI_IMAGE                   = ('oci_image', '%s/oci')
    OCI_BLOBS                   = ('oci_blobs', '%s/oci/blobs')
    OCI_BLOBS_SHA               = ('oci_blobs_sha', '%s/oci/blobs/%s')
    OCI_INDEX                   = ('oci_index', '%s/oci/index.json')
    OCI_IMAGE_LAYOUT_VERSION    = ('oci_image_layout_version', '%s/oci/oci-layout')  
    TARS                        = ('tars', '%s/tars' )
    SCRATCH                     = ('scratch', '%s/scratch')

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
            cls.ROOT[0]:                        cls.ROOT[1] % (temp_dir),
            cls.ROOTFS[0]:                      cls.ROOTFS[1] % (temp_dir),
            cls.IMAGE[0]:                       cls.IMAGE[1] % (temp_dir),
            cls.FILESYSTEM[0]:                  cls.FILESYSTEM[1] % (temp_dir),
            cls.ARTIFACTS[0]:                   cls.ARTIFACTS[1] % (temp_dir),
            cls.OCI_IMAGE[0]:                   cls.OCI_IMAGE[1] % (temp_dir),
            cls.OCI_BLOBS[0]:                   cls.OCI_BLOBS[1] % (temp_dir),
            cls.OCI_BLOBS_SHA[0]:               cls.OCI_BLOBS_SHA[1] %(temp_dir, sha),
            cls.OCI_INDEX[0]:                   cls.OCI_INDEX[1] % (temp_dir),
            cls.OCI_IMAGE_LAYOUT_VERSION[0]:    cls.OCI_IMAGE_LAYOUT_VERSION[1] % (temp_dir),
            cls.TARS[0]:                        cls.TARS[1] % (temp_dir), # temp location for tars
            cls.SCRATCH[0]:                     cls.SCRATCH[1] % (temp_dir)
            #'artifacts':   '%s/rootfs/artifacts' % (temp_dir),
        }
        skip = [cls.ROOT[0], cls.OCI_INDEX[0], cls.OCI_IMAGE_LAYOUT_VERSION[0]]
        ## dont need to check if dir already exists -- tmp file
        for key, dir in temp.items():
            #skip some dirs
            if key in skip:
                continue
            os.mkdir(dir)
        return TemporaryDirs(temp)

    def delete(self):
        """
        Delete temporary directory.
        """
        shutil.rmtree(self._dirs[self.ROOT[0]])

    def get_path(self, key) -> str: 
        """
        Get a path managed by TemporaryDirs
        :return path
        :raise ValueError if invalid key
        """
        if key not in self._dirs:
            raise ValueError("Invalid directory key: %s" % (key))
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

def _create_digest(
        path="",
        algo: Algorithm = None,
        buff_size = 1024 * 60):
    """
    _create_digest and _validate()
    :raise KraftError if path is not accessible or digest is invalid
    """
    if not os.path.isfile(path) | os.path.isdir(path):
        raise KraftError("Error path is not accesible")
    digest = ""
    digester = algo.digester()
    with open(path, 'rb') as f:
        data = f.read(buff_size)
        while data:
            digester.hash.update(data)
            data = f.read(buff_size)
    digest = digester.digest()
    try:
        _validate(digest)
    except KraftError as e:
        raise e
    return digest

def _move_digest(temp_path=None, digest_path=None):
    """
    _move_digest from `temp_path` to `digest_path`
    :raise KraftError if path strings are invalid
    :raise KraftError if no file at temp path
    """
    if None in (temp_path, digest_path):
        raise KraftError("Error paths must not be None")
    if not os.path.isfile(temp_path):
        raise KraftError("Unable to access file at path %s" % temp_path)
    shutil.move(temp_path, digest_path)

def _make_tar(path: str, files: List[Tuple[str, str]] = None, compression=""):
    """
    _make_tar at `path` containing `files`
    :param path to to tar archive
    :param files is a tuple of (path_to_file, arcname), encapsulating a path to a file
        and the path the file will be stored at in the archive
    :param compression is one of the `compression_algorithms` keys
    :raise KraftError if invalid compression key is chosen
    :raise KraftError if digest fails to validate
    """
    if not compression in compression_algorithms.keys():
        raise KraftError("Unsupported compression algorithm: %s" % compression)
    with tarfile.open(path, compression_algorithms[compression]) as tar:
        for file in files:
            tar.add(file[0], arcname=file[1])

class Packager:
    def __init__(
        self,
        image: ImageWrapper = None,
        filesystem: FilesystemWrapper = None,
        artifacts: List[ArtifactWrapper] = None,
        digest_algorithm=default_digest_algorithm,
        hash_buffer_size=HASH_BUFF_SIZE,
        temporary_dirs: TemporaryDirs = None,
        compression_algorithm = DEFAULT_COMPRESSION
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
        self._digest_algo = Algorithm(digest_algorithm)
        self._hash_buff_size = hash_buffer_size
        self._temporary_dirs = temporary_dirs
        self._compression_algo = compression_algorithm
        self._index = None
        self._manifest = None
        self._image_config = None
        self._filesystem_tar_digest = None
        self._image_layout = None

    def create_oci_filesystem(self) -> DigestWrapper:
        """
        create_oci_filesystem creates OCI Image rootfs, tars it and creates a digest.
        :return DigestWrapper over tar'ed rootfs
        """
        image_name = os.path.basename(self._image.path)
        image_path = '%s/%s' %(self._temporary_dirs.get_path('image'), image_name) 
        shutil.copy2(self._image.path, image_path)
        if self._filesystem:
            fs_name = os.path.basename(self._filesystem.path)
            shutil.copy(self._image.path, '%s/%s'
                        %(self._temporary_dirs.get_path('filesystem'), fs_name))
        ## copy artifacts/filesystem
        rootfs_artifacts = self._temporary_dirs.get_path(TemporaryDirs.ARTIFACTS[0]) 
        if self._artifacts:
            for artifact in self._artifacts:
                artifact_name = os.path.basename(artifact.path)
                artifact_path = "%s/%s" % (rootfs_artifacts, artifact_name)
                shutil.copy(artifact.path, artifact_path)
        ## tar up rootfs
        tar_rootfs_path = '%s/%s' % (self._temporary_dirs.get_path('tars'), 'rootfs.tar.gz')
        tar_tuple = (self._temporary_dirs.get_path('rootfs'), '/rootfs')
        _make_tar(tar_rootfs_path, [tar_tuple], self._compression_algo)
        digest = None
        try:
            digest = _create_digest(tar_rootfs_path, self._digest_algo)
        except KraftError as e:
            raise e
        self._filesystem_tar_digest = digest
        #move to oci dir
        digest_path = "%s/%s" %(self._temporary_dirs.get_path('oci_blobs_sha'), digest.encoded())
        _move_digest(tar_rootfs_path, digest_path)
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
        digest = None
        try:
            digest = _create_digest( path = scratch_file, algo = self._digest_algo)
        except KraftError as e:
            raise e
        digest_path = "%s/%s" %(self._temporary_dirs.get_path('oci_blobs_sha'), digest.encoded())
        _move_digest(scratch_file, digest_path)
        return DigestWrapper(
            digest = digest,
            path = digest_path,
            media_type = MediaType.MediaTypeImageConfig
        )

    def create_oci_manifest(self,
                            config_digest: DigestWrapper,
                            layer_digests: List[DigestWrapper]) -> DigestWrapper:
        conf_descriptor = config_digest.descriptor
        layer_descriptors = [dw.descriptor for dw in layer_digests]
        layers_d = [dw.to_dict() for dw in layer_descriptors]
        annotations = {}
        # TODO: check architecture and manifest are valid
        if self._image.architecture:
            annotations["architecture"] = self._image.architecture
        if self._image.platform:
            annotations["platform"] = self._image.platform
        manifest = Imagev1.Manifest(
            manifestConfig=conf_descriptor.to_dict(),
            layers=layers_d,
            annotations=annotations,
            schemaVersion = Versioned(2)
        )
        # write 
        scratch_file = "%s/manifest.json" %(self._temporary_dirs.get_path('scratch'))
        with open(scratch_file, "w") as f:
            f.write(manifest.to_json())
        digest = None
        try:
            digest = _create_digest(path = scratch_file, algo = self._digest_algo)
        except KraftError as e:
            raise e
        digest_path = self._temporary_dirs.get_blob_path(digest.encoded())
        _move_digest(scratch_file, digest_path)
        return DigestWrapper(
            digest = digest,
            path = digest_path,
            media_type = MediaType.MediaTypeImageManifest
        )

    def create_index(self, manifest_digests: List[DigestWrapper]) -> str:
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

    def create_oci_archive(self, out: str = "", path: str = ""):
        """
        Create an oci archive from artifacts.
        :param path to oci directory to be archived
        :param out where archive should be stored.
        """
        if not path:
            path = self._temporary_dirs.get_path(TemporaryDirs.OCI_IMAGE[0])
        files = [ (path, "/") ]
        try:
            _make_tar(out, files, self._compression_algo)
        except KraftError as e:
            raise e

    def create_oci_layout(self):
        """
        Create OCI Image Layout file.
        """
        _ = self
        self._image_layout = ImageLayout()
        scratch_file = "%s" %(self._temporary_dirs.get_path(
            TemporaryDirs.OCI_IMAGE_LAYOUT_VERSION[0]
        ))
        with open(scratch_file, "w") as f:
            f.write(self._image_layout.to_json())

    def clean_temporary_dirs(self):
        """
        Delete temporary directories
        """
        self._temporary_dirs.delete()
        

