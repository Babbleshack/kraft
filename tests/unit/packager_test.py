import os
from kraft.package.package import Packager
from kraft.package.package import ImageWrapper
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

        #TODO add uk_conf to image
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
        content = packager.create_oci_filesystem()
        self.content = content
        print(content)
        self.assertEqual(EXPECTED_HASH_VALUE, content['digest'].encoded())
        self.assertTrue(os.path.isfile(content['path']))

    # TODO delete temp dir
    #def tearDown(self)
    #    os.rmdir(self.content['path']) 

if __name__ == '__main__':
    unittest.main()
