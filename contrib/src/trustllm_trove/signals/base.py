from datatrove.pipeline.filters.base_filter import BaseFilter

class Bound:
    def __init__(self, low=None, high=None, accept_none=False):
        self.low_pass = (lambda x: low <= x) if low is not None  else (lambda x: True)
        self.high_pass = (lambda x: x <= high) if high is not None else (lambda x: True)
        self.none_pass = (lambda x: accept_none)

    def __call__(self, x):
        if x is None:
            if not self.none_pass(x):
                return False, 'is None'
        else:
            if not self.low_pass(x):
                return False, 'below threshold'
            if not self.high_pass(x):
                return False, 'above threshold'
        return True

class Record(object):
    def __init__(self, doc):
        self.doc = doc

    def filter(self, **bounds):
        for key, bound in bounds.items():
            value = getattr(self, key)()
            self.doc.metadata[f'{key}'] = value
            match bound(value):
                case (False, reason):
                    self.doc.metadata['filter_value'] = value
                    return False, f'{key} {reason}'
                case True:
                    continue
        return True

    def signals(self, *names):
        return {key: getattr(self, key)() for key in names}

class TrustLLMFilter(BaseFilter):
    name = 'TrustLLM base filter Filter'

    def __init__(self, exclusion_writer=None, record=None, bounds=None):
        super().__init__(exclusion_writer)
        self.record = record
        self.bounds = bounds

    def filter(self, doc):
        return self.record(doc).filter(**self.bounds)
