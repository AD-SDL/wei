"""Provides base classes for WEI's pytest tests"""
import unittest


class TestWEI_Base(unittest.TestCase):
    """Base class for WEI's pytest tests"""

    pass


class TestImports(TestWEI_Base):
    """Test Imports"""

    def test_wei_import(self):
        """Test WEI version"""
        import wei

        assert wei.__version__


if __name__ == "__main__":
    unittest.main()
