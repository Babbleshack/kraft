import os
from kraft.package.package import Packager
from kraft.package.oci.opencontainers.digest import SHA256 
from .. import unittest

EXPECTED_HASH_VALUE = "c1ac6403f2519d86296264021abc18255b5e83c389172a58c819c91079a3041f"
    #def __init__(
    #    self,
    #    image="",
    #    filesystem="",
    #    uk_conf="",
    #    artifacts=[],
    #    digest_algorithm=default_digest_algorithm,
    #    hash_buffer_size=HASH_BUFF_SIZE
    #):

class PackagerTest(unittest.TestCase):
    def test_create_oci_image(self):
        packager = Packager(
            image="./tests/artifacts/image",
            uk_conf="./tests/artifacts/image",
            digest_algorithm=SHA256
        )
        content = packager.create_oci_filesystem()
        print(content)
        self.assertEqual(EXPECTED_HASH_VALUE, content['digest'].encoded())
        self.assertTrue(os.path.isfile(content['path']))

if __name__ == '__main__':
    unittest.main()
