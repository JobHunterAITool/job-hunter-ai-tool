import time
import pytest

@pytest.fixture(scope="session", autouse=True)
def print_runtime_before_and_after_session():
    start = time.time()
    print("\n[pytest runtime] Test session started...")
    yield
    end = time.time()
    elapsed = end - start
    print(f"\n[pytest runtime] Test session finished in {elapsed:.3f} seconds ({time.strftime('%H:%M:%S', time.gmtime(elapsed))})\n")
