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
import sys
import os
import click
from kraft.package.package import (
    ImageWrapper,
    FilesystemWrapper,
    ArtifactWrapper,
    Packager,
    compression_algorithms
)
from opencontainers.digest.algorithm import algorithms 
from kraft.error import KraftError
from kraft.logger import logger

def kraft_package(ctx, kernel=None, arch=None, platform=None, config=None,
                  filesystem_path=None, artifact_paths=[], hash_algo=None, compression=None):
    if hash_algo not in algorithms.keys():
        raise KraftError("Error invalid hash algorithm, valid algorithms: %s" %
                         ", ".join(algorithms.keys()))
    fs = None
    if filesystem_path:
        fs = FilesystemWrapper(path = filesystem_path)
    artifacts = []
    for artifact in artifact_paths:
        artifacts.append( ArtifactWrapper(path=artifact))
    image = ImageWrapper(
        path=kernel,
        architecture=arch,
        platform=platform,
        uk_conf=config
    )
    try:
        packager = Packager(
            image=image,
            filesystem=fs,
            artifacts=artifacts,
            digest_algorithm=hash_algo,
            compression_algorithm=compression
        )
        fs_dw = packager.create_oci_filesystem()
        conf_dw = packager.create_oci_config(fs_dw)
        manifest_dw = packager.create_oci_manifest(config_digest=conf_dw,
                                                   layer_digests=[fs_dw])
        packager.create_index(manifest_digests=[manifest_dw])
        packager.create_oci_layout()
        if not os.path.isdir("./package"):
            os.mkdir("./package")
        package_path = "./package/%s" % os.path.basename(image.path)
        packager.create_oci_archive(package_path)
        packager.clean_temporary_dirs()
    except Exception as e:
        raise e


#TODO we can inteligently guess config and image paths?
@click.command('package', short_help='package Unikraft unikernel as a OCI-Image')
@click.option('--filesystem', '-fs', 'filesystem_path')
@click.option('--artifact', '-r', 'artifact_paths', 
              multiple=True,
              type=click.Path(exists=True, readable=True))
@click.option('--hash-type', '-h', default="sha256",
              type=click.Choice(algorithms.keys(), case_sensitive=False))
@click.option('--compression-algorithm', '-h', 'compression', default="gzip",
              type=click.Choice(compression_algorithms.keys(), case_sensitive=False))
@click.argument('image',
                type=click.Path(exists=True),
                required=True)
@click.argument('architecture', required=True)
@click.argument('platform', required=True)
@click.argument('config',
                type=click.Path(exists=True),
                required=True)
@click.pass_context
def cmd_package(ctx, image=None, architecture=None, platform=None, config=None,
                filesystem_path=None, artifact_paths=[], hash_type=None,
                compression=None):
    """
    Packages a Unikraft application as an OCI Image
    """
    hash_type = hash_type.lower()
    compression = compression.lower()
    try:
        kraft_package(
            ctx,
            kernel=image,
            arch=architecture,
            platform=platform,
            config=config,
            filesystem_path=filesystem_path,
            artifact_paths=artifact_paths,
            hash_algo=hash_type,
            compression=compression
        )
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())
        sys.exit(1)
