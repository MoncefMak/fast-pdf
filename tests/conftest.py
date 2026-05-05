"""Project-wide pytest configuration.

Currently exposes a single CLI flag, --regenerate-golden, used by
tests/test_golden.py to refresh the SHA-256 fixtures in
tests/golden/expected/.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regenerate-golden",
        action="store_true",
        default=False,
        help="rewrite tests/golden/expected/*.sha256 from the current build",
    )


@pytest.fixture
def regenerate_golden(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--regenerate-golden"))
