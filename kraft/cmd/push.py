# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Laurentiu Barbulescu <lrbarbulescu@gmail.com>
#
# Copyright (c) 2021, NEC Europe Laboratories GmbH., NEC Corporation.
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

from opencontainers.distribution.reggie import *
from kraft.logger import logger
import click
import sys
import os
import subprocess
import tarfile
import json

default_path = './package/'
default_url = 'http://10.16.4.30:80'
index_path = 'index.json'
default_project = 'library'

# TODO: add version tag for repositories
@click.command('push', short_help='Push an OCI-Image on Harbor')

@click.option(
    '--image', '-i', 'image',
    help='Specify the OCI-Image path. Default: ./package/*',
    metavar="IMAGE_PATH"
)

@click.option(
    '--name', '-n', 'name',
    help='Specify the repository name. Default: IMAGE_NAME',
    metavar="REPOSITORY"
)

@click.option(
    '--server', '-s', 'server',
    help='Specify the Harbor instance url',
    metavar="URL"
)

@click.pass_context
def cmd_push(ctx, image=None, name=None, server=None):
    """
    Push an OCI-Image on Harbor
    """

    if image is None:
        output = subprocess.check_output(['ls', default_path])
        
        files = output.decode('utf-8').split()
        if len(files) != 1:
            logger.critical('Operation failed, multiple files found.')
            if ctx.obj.verbose:
                import traceback
                logger.critical(traceback.format_exc())
            sys.exit(1)
        else:
            image = default_path + files[0]

    if name is None:
        tokens = image.split('/')
        name = tokens[len(tokens)-1]

    if server is None:
        server = default_url

    try:
        kraft_push(
            image=image,
            name=name,
            server=server
        )
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)

@click.pass_context
def kraft_push(ctx, image=None, name=None, server=None):

    cmd = 'ls ' + image + ' > /dev/null 2>&1'
    rc = os.system(cmd)
    if rc != 0:
        raise Exception('Image not found.')

    rc = tarfile.is_tarfile(image)
    if not rc:
        raise Exception('Bad OCI-Image format.')

    client = NewClient(server,
                       WithUsernamePassword('admin', 'Harbor12345'),
                       WithDefaultName(name),
                       WithDebug(True))

    # req = client.NewRequest("GET", "/api/v2.0/ping")
    # print(req)
    # response = client.Do(req)
    # print(response._content)

    t = tarfile.open(image)

    index_fd = t.extractfile(index_path)
    index_json = json.load(index_fd)
    
    manifest_digest = index_json['manifests'][0]['digest']
    tokens = manifest_digest.split(':')
    manifest_path = 'blobs/' + tokens[0] + '/' + tokens[1]
    # print(manifest_path)

    manifest_fd = t.extractfile(manifest_path)
    manifest_json = json.load(manifest_fd)

    config = manifest_json['config']
    layers = manifest_json['layers']
    blobs = [config] + layers

    # push the blobs specified
    for blob in blobs:
        blob_digest = blob['digest']
        tokens = blob_digest.split(':')
        blob_path = 'blobs/' + tokens[0] + '/' + tokens[1]
        # print(blob_path)
        # prepare the request to upload
        req = client.NewRequest("POST", "/v2/" + default_project + "/<name>/blobs/uploads/")
        # print(req)
        response = client.Do(req)
        # print(response.headers['Location'])

        with t.extractfile(blob_path) as blob_fd:
            data = blob_fd.read()

        req = (client.NewRequest("PUT", response.GetRelativeLocation()).
                    SetHeader("Content-Type", blob['mediaType']). # "application/octet-stream").
                    SetHeader("Content-Length", str(len(data))).
                    SetQueryParam("digest", blob_digest).
                    SetBody(data))
        # print(req)
        response = client.Do(req)
        # print(response.headers['Location'])

    # upload the manifest
    req = (client.NewRequest("PUT", "/v2/" + default_project + "/<name>/manifests/<reference>",
                WithReference("latest")).
                SetHeader("Content-Type", index_json['manifests'][0]['mediaType']). # "application/vnd.oci.image.manifest.v1+json").
                SetBody(manifest_json))
    response = client.Do(req)
