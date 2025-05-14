from contextlib import contextmanager

try:
    from transformers.modeling_utils import init_empty_weights
except ImportError:
    @contextmanager
    def init_empty_weights():
        # Fallback to a no-op if init_empty_weights is not available
        yield
