import unittest


class TestWEI_Base(unittest.TestCase):
    pass


class TestImports(TestWEI_Base):
    def test_wei_import(self):
        import wei

        assert wei.__version__


if __name__ == "__main__":
    unittest.main()
