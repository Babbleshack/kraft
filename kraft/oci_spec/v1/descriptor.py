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

class Descriptor:
    """
    Descriptor describes the disposition of targeted content.
    This structure provides `application/vnd.oci.descriptor.v1+json` mediatype
    when marshalled to JSON.
    """
    def __init__(self, media_type=None, digest=Digest(), size=0, urls=None,
                  annotations=None, platform=None):
        #TODO: define Digest class
        self._media_type = media_type
        self._digest = digest
        self._size = size
        self._urls = urls
        self._annotations = annotations
        self._platform = platform

    @property
    def media_type(self):
        """media_type is the media type of the object this schema refers to."""
        return self._media_type

    @property
    def digest(self):
        """
        digest is the digest of the targeted content.
        @see https://github.com/opencontainers/go-digest
        """
        return self._digest

    @property
    def size(self):
        """
        size specifies the size in bytes of the blob
        """
        return self._size

    @property
    def urls(self):
        """
        urls specifies a list of URLs from which this object MAY be downloaded
        """
        return self._urls

    @property
    def annotations(self):
        """
        Annotations contains arbitrary metadata relating to the targeted
        content.
        """
        return self._annotations

    @property
    def platform(self):
        """
        Platform describes the platform which the image in the manifest runs on.
        This should only be used when referring to a manifest.
        """
        #TODO: move platform to ManifestDescriptor subclass
        return self._platform

    class Platform:
        """
        Platform describes the platform which the image in the manifest runs on.
        """
        def __init__(self, architecture="", os="", os_version=None,
                     os_features=None, variant=None):
            self._architecture = architecture
            self._os = os
            self._os_version = os_version
            self._os_features = os_features 
            self._variant = variant

        @property
        def architecture(self):
            """
            Architecture field specifies the CPU architecture, for example
            `x86_64` or `arm64`.
            """
            return self._architecture

        @property
        def os(self):
            """
            os specifies the operating system, e.g. `linux`, `windows`
            """
            return self._os
        
        @property
        def os_version(self):
            """
            os_version is an optional fields describing version of operating system
            for example linux kernel version or windows release number
            """
            return self._os_version

        @property
        def os_features(self):
            """
            os_features is an array of string describing required os_features
            """
            return self._os_features

        @property
        def variant(self):
            """
            variant is an optional field describing version of cpu
            e.g. ARMv8
            """
            return self._variant

