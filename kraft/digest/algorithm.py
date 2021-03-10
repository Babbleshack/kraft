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
import hashlib
import re
import io
from enum import Enum, unique

@unique
class SupportedAlgorithms(Enum):
    """
    Enumerate supported digest algorithms.
    """
    SHA256 = 1
    SHA384 = 2
    SHA512 = 3

class Algorithm():
    """
    Algorithm is a wrapper class for managing supported
    digest secure hashes.
    """
    def __init__(self):
        self._anchored_encoded_regex = {
            SupportedAlgorithms.SHA256: re.compile("^[a-f0-9]{64}"),
            SupportedAlgorithms.SHA384: re.compile("^[a-f0-9]{96}"),
            SupportedAlgorithms.SHA512: re.compile("^[a-f0-9]{128}")
        }


    def available(self):
        """
        return true if hash algo is available for use as digest,
        else return false.
        If return false Digester and Hash will also return None.
        """
        _ = self
        raise NotImplementedError()

    def __string__(self):
        """
        return digest string
        """
        _ = self
        raise NotImplementedError()

    def size(self):
        """
        return size in bytes of hash
        """
        _ = self
        raise NotImplementedError()

    def set(self, algo):
       """
       Set the algorithm to be used for digest.
       """
       _ = self
       _ = algo
       raise NotImplementedError()

    def build_digester(self):
        """
        return a `Digester` from this Algorithm
        """
        _ = self
        raise NotImplementedError()

    def hash(self):
        """
        returns a hash implemetation as used by the algorithm. If not available, the method
        will raise a `XXXError()`. Call Algorithm.Available() before calling.
        """
        _ = self
        raise NotImplementedError()

    def encode(self, bytes=[]):
        """
        encode encodes raw bytes of a digest, typically by calling hashlib's `digest()` function
        over the the encoed portion of the digest string.
        """
        # TODO: improve the comment for this methods
        _ = bytes
        _ = self
        raise NotImplementedError()

    def from_reader(self, reader=io.TextIOWrapper):
        """
        return digest of reader using the alorithm
        """
        _ = self
        _ = reader
        raise NotImplementedError()

    def from_bytes(self, bytes=[]):
        """
        return digest over the bytes
        """
        _ = self
        _ = bytes 
        raise NotImplementedError()

    def from_string(self, str=""):
        """
        return digest over a string
        """
        _ = self
        _ = str
        raise NotImplementedError()

    def validate(self, encoded): 
        """
        validate encoded portion of string
        """
        _ = self
        _ = encoded
        raise NotImplementedError()
