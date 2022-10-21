import unittest


class TestWEI_Base(unittest.TestCase):
    pass


class TestImports(TestWEI_Base):
    def test_rpl_wei_import(self):
        import rpl_wei

        assert rpl_wei.__version__


if __name__ == "__main__":
    unittest.main()
