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

import click
import sys
import os
import subprocess

from kraft.logger import logger

default_path = './package/'
default_server = '10.16.4.30/library/'

# TODO: add version tag for repositories
@click.command('push', short_help='Push an OCI-Image on Harbor')

@click.option(
    '--image', '-i', 'image',
    help='Specify the OCI-Image path. Default: ./package/*',
    metavar="IMAGE"
)

@click.option(
    '--name', '-n', 'name',
    help='Specify the repository name. Default: IMAGE_NAME',
    metavar="REPOSITORY"
)

@click.option(
    '--server', '-s', 'server',
    help='Specify the Harbor instance and project',
    metavar="IP/PROJECT/"
)

@click.pass_context
def cmd_push(ctx, image=None, name=None, server=None):
    """
    Push an OCI-Image on Harbor
    """

    if image is None:
        output = subprocess.check_output(['ls', default_path]).decode('utf-8')
        
        files = output.split()
        if len(files) != 1:
            logger.critical('Operation failed, multiple files found.')
            if ctx.obj.verbose:
                import traceback
                logger.critical(traceback.format_exc())
            sys.exit(1)
        else:
            image = default_path + files[0]
            if name is None:
                name = files[0]
    if server is None:
        server = default_server

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

    cmd = 'docker -v > /dev/null 2>&1'
    rc = os.system(cmd)
    if rc != 0:
        raise Exception('Missing docker client.')

    cmd = 'ls ' + image + ' > /dev/null 2>&1'
    rc = os.system(cmd)
    if rc != 0:
        raise Exception('Image not found.')

    cmd = 'file ' + image + ' | grep "tar archive" > /dev/null 2>&1'
    rc = os.system(cmd)
    if rc != 0:
        raise Exception('Bad OCI-Image format.')

    cmd = 'docker import ' + image + ' ' + name
    os.system(cmd)

    repo_name = server + name
    cmd = 'docker tag ' + name + ' ' + repo_name + '> /dev/null 2>&1'
    os.system(cmd)

    cmd = 'docker push ' + repo_name
    os.system(cmd)

    cmd = 'docker rmi -f ' + name + ' ' + repo_name + '> /dev/null 2>&1'
    os.system(cmd)
