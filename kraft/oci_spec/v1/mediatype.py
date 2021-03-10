# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Dominic Lindsay <dcrl94@gmail.com>
#
# Copyright (c) 2020, NEC Europe Laboratories Gmb_h., NEC Corporation.
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

"""
MEDIA_TYPE_DESCRIPTOR specifies the media type for a content descriptor.
"""
MEDIA_TYPE_DESCRIPTOR = "application/vnd.oci.descriptor.v1+json"

"""
MEDIA_TYPE_LAYOUT_HEADER specifies the media type for the oci-layout.
"""
MEDIA_TYPE_LAYOUT_HEADER = "application/vnd.oci.layout.header.v1+json"

"""
MEDIA_TYPE_IMAGE_MANIFEST specifies the media type for an image manifest.
"""
MEDIA_TYPE_IMAGE_MANIFEST = "application/vnd.oci.image.manifest.v1+json"

"""
MEDIA_TYPE_IMAGE_INDEX specifies the media type for an image index.
"""
MEDIA_TYPE_IMAGE_INDEX = "application/vnd.oci.image.index.v1+json"

# MEDIA_TYPE_IMAGE_LAYER is the media type used for layers referenced by the manifest.
"""
MEDIA_TYPE_IMAGE_LAYER is the media type used for layers referenced by the manifest.
"""
MEDIA_TYPE_IMAGE_LAYER = "application/vnd.oci.image.layer.v1.tar"

"""
MEDIA_TYPE_IMAGE_LAYER_GZIP is the media type used for gzipped layers
referenced by the manifest.
"""
MEDIA_TYPE_IMAGE_LAYER_GZIP = "application/vnd.oci.image.layer.v1.tar+gzip"

"""
MEDIA_TYPE_IMAGE_LAYER_ZSTD is the media type used for zstd compressed
layers referenced by the manifest.
"""
MEDIA_TYPE_IMAGE_LAYER_ZSTD = "application/vnd.oci.image.layer.v1.tar+zstd"

"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE is the media type for layers referenced by
the manifest but with distribution restrictions.
"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE = "application/vnd.oci.image.layer.nondistributable.v1.tar"

"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE_GZIP  is the media type for
gzipped layers referenced by the manifest but with distribution
restrictions.
"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE_GZIP = "application/vnd.oci.image.layer.nondistributable.v1.tar+gzip"

"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE_ZSTD is the media type for zstd
compressed layers referenced by the manifest but with distribution
restrictions.
"""
MEDIA_TYPE_IMAGE_LAYER_NON_DISTRIBUTABLE_ZSTD = "application/vnd.oci.image.layer.nondistributable.v1.tar+zstd"

"""
MEDIA_TYPE_IMAGE_CONFIG specifies the media type for the image
configuration.
"""
MEDIA_TYPE_IMAGE_CONFIG = "application/vnd.oci.image.config.v1+json"
