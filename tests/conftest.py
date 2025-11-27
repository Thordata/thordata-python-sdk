# tests/conftest.py

"""
Pytest configuration for asynchronous tests.

This file ensures that the pytest-asyncio plugin is always loaded,
so that:
- asyncio_mode in pytest.ini is recognized
- @pytest.mark.asyncio works as expected
- async fixtures are properly handled
"""

pytest_plugins = ("pytest_asyncio",)