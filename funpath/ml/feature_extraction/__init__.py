from funpath.html_extraction import DOMTree
from functools import wraps

FEATURE_EXTRACTORS = {}

NOT_CLASSIFIED_ELEMENT_NAME = 'OTHER'

def feature_extractor(fn):
    """
        Register a feature extractor so that it
        becomes available for classifiers.
    """
    FEATURE_EXTRACTORS[fn.__name__] = fn
    @wraps(fn)
    def execute(*args, **kwargs):
        return fn(*args, **kwargs)
    return execute


def apply_extractors(names, **ctx):
    """
        Apply the given feature extractors and
        returns a dict with their names and results
    """
    return {
        name: FEATURE_EXTRACTORS[name](**ctx)
        for name in names
    }

