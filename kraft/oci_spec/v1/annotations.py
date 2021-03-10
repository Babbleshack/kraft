"""ANNOTATION_CREATED is the annotation key for the date and time on which the the image was built (data-time as defined by RFC 3339)."""
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

ANNOTATION_CREATED = "org.opencontainers.image.created"

"""ANNOTATION_AUTHORS is the annotation key for the contact details of the people or organsiation responsible for the image (freeform string)."""
ANNOTATION_AUTHORS = "org.opencontainers.image.authors"

"""ANNOTATION_URL is the annotation key for the URL to find more information on the image."""
ANNOTATION_URL = "org.opencontainers.image.url"

"""ANNOTATION_DOCUMENTATION is the annotation key for the URL to get documentation on the image."""
ANNOTATION_DOCUMENTATION = "org.opencontainers.image.documentation"

"""ANNOTATION_SOURCE is the annotation key for the URL to get source code for building the image."""
ANNOTATION_SOURCE = "org.opencontainers.image.source"

"""
ANNOTATION_VERSION is the annotation key for the version of the packaged software.
The version MAY match a label or tag in the source code repository.
The version MAY be Semantic versioning-compatible.
"""
ANNOTATION_VERSION = "org.opencontainers.image.version"

"""ANNOTATION_REVISION is the annotation key for the source control revision identifier for the packaged software."""
ANNOTATION_REVISION = "org.opencontainers.image.revision"

"""ANNOTATION_VENDOR is the annotation key for the name of the distributing entity, organization or individual."""
ANNOTATION_VENDOR = "org.opencontainers.image.vendor"

"""ANNOTATION_LICENSES is the annotation key for the license(s) under which contained software is distributed as an SPDX License Expression."""
ANNOTATION_LICENSES = "org.opencontainers.image.licenses"

"""
ANNOTATION_REF_NAME is the annotation key for the name of the reference for a target.
SHOULD only be considered valid when on descriptors on `index.json` within image.
"""
ANNOTATION_REF_NAME = "org.opencontainers.image.ref.name"

"""ANNOATION_TITLE is the annotation key for the human-readable title for the image."""
ANNOTATION_TITLE = "org.opencontainers.image.title"

"""ANNOTATION_DESCRIPTION is the annotation key for the human-readable description fothe software package image."""
ANNOTATION_DESCRIPTION = "org.opencontainers.image.description"
