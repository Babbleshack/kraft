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
index_path = 'index.json'
default_url = 'http://10.16.4.30:80'
default_project = 'library'
default_user = 'admin'
default_passwd = 'Harbor12345'

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
    help='Specify a Harbor instance url',
    metavar="http://URL:PORT"
)

@click.option(
    '--project', '-p', 'project',
    help='Specify the project',
    metavar="PROJECT"
)

@click.option(
    '--user', '-u', 'user',
    help='Specify the user',
    metavar="USER"
)

@click.option(
    '--password', '-pw', 'passwd',
    help='Specify the password',
    metavar="PASSWORD"
)

@click.pass_context
def cmd_push(ctx, image=None, name=None, server=None, project=None, user=None, passwd=None):
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

    if project is None:
        project = default_project

    if user is None:
        user = default_user

    if passwd is None:
        passwd = default_passwd

    try:
        kraft_push(
            image=image,
            name=name,
            server=server,
            project=project,
            user=user,
            passwd=passwd
        )
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)

@click.pass_context
def kraft_push(ctx, image=None, name=None, server=None, project=None, user=None, passwd=None):

    cmd = 'ls ' + image + ' > /dev/null 2>&1'
    rc = os.system(cmd)
    if rc != 0:
        raise Exception('Image not found.')

    rc = tarfile.is_tarfile(image)
    if not rc:
        raise Exception('Bad OCI-Image format.')

    # if you provide a custom server, but you don't provide a
    # custom user, try to connect to it without credentials
    if server != default_url and user == default_user:
        client = NewClient(server,
                           WithDefaultName(name))
    else:
        client = NewClient(server,
                           WithUsernamePassword(user, passwd),
                           WithDefaultName(name))

    t = tarfile.open(image)

    index_fd = t.extractfile(index_path)
    index_json = json.load(index_fd)
    
    manifest_digest = index_json['manifests'][0]['digest']
    tokens = manifest_digest.split(':')
    manifest_path = 'blobs/' + tokens[0] + '/' + tokens[1]

    manifest_fd = t.extractfile(manifest_path)
    manifest_json = json.load(manifest_fd)

    config = manifest_json['config']
    layers = manifest_json['layers']
    blobs = [config] + layers

    # push the config and layers blobs
    for blob in blobs:
        # prepare the request to upload
        req = client.NewRequest("POST", "/v2/" + project + "/<name>/blobs/uploads/")
        response = client.Do(req)
        if response.status_code != 202:
            raise Exception('[POST] response', response.status_code)

        blob_digest = blob['digest']
        tokens = blob_digest.split(':')
        blob_path = 'blobs/' + tokens[0] + '/' + tokens[1]

        with t.extractfile(blob_path) as blob_fd:
            data = blob_fd.read()

        # upload the blob
        req = (client.NewRequest("PUT", response.GetRelativeLocation()).
                    SetHeader("Content-Type", blob['mediaType']).
                    SetHeader("Content-Length", str(len(data))).
                    SetQueryParam("digest", blob_digest).
                    SetBody(data))
        response = client.Do(req)
        if response.status_code != 201:
            raise Exception('[PUT] response', response.status_code)

    # upload the manifest
    req = (client.NewRequest("PUT", "/v2/" + project + "/<name>/manifests/<reference>",
                WithReference("latest")).
                SetHeader("Content-Type", index_json['manifests'][0]['mediaType']).
                SetBody(manifest_json))
    response = client.Do(req)
    if response.status_code != 201:
            raise Exception('[PUT] response', response.status_code)
