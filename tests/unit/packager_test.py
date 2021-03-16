import os
import tempfile
import hashlib
from kraft.package.oci.opencontainers.digest  import (
    Canonical as default_digest_algorithm,
)
from kraft.package.package import Packager
from kraft.package.package import ImageWrapper
from kraft.package.oci.opencontainers.digest import SHA256 
from .. import unittest

EXPECTED_HASH_VALUE = "c1ac6403f2519d86296264021abc18255b5e83c389172a58c819c91079a3041f"

def tree_printer(root):
    for root, dirs, files in os.walk(root):
        for d in dirs:
            print(os.path.join(root, d))
        for f in files:
            print(os.path.join(root, f))

class PackagerTest(unittest.TestCase):
    def test_create_oci_image(self):
        image = ImageWrapper(
            path="./tests/artifacts/image",
            architecture="x86_64",
            platform="kvm",
            uk_conf="./tests/artifacts/image"
        )
        packager = Packager(
            image=image,
            digest_algorithm=SHA256
        )
        fs_dw = packager.create_oci_filesystem()
        #print(fs_dw.to_descriptor().to_json())
        self.assertEqual(EXPECTED_HASH_VALUE, fs_dw.digest)
        self.assertTrue(os.path.isfile(fs_dw.path))
        packager._temporary_dirs.delete()

    def test_build_oci(self):
        _ = self
        image = ImageWrapper(
            path="./tests/artifacts/image",
            architecture="x86_64",
            platform="kvm",
            uk_conf="./tests/artifacts/image"
        )
        packager = Packager(
            image=image,
            digest_algorithm=SHA256
        )
        fs_dw = packager.create_oci_filesystem()
        conf_dw = packager.create_oci_config(fs_dw)
        manifest_dw = packager.create_oci_manifest(config_digest=conf_dw,
                                                   layer_digests=[fs_dw])
        packager.create_index(manifest_digests=[manifest_dw])
        tree_printer(packager._temporary_dirs.get_path(packager._temporary_dirs.ROOT[0]))
        packager._temporary_dirs.delete()
        
if __name__ == '__main__':
    unittest.main()
