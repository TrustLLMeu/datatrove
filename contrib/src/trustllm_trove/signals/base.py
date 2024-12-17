from datatrove.pipeline.filters.base_filter import BaseFilter

class Bound:
    def __init__(self, low=None, high=None, accept_none=False):
        self.low = low
        self.high = high
        self.accept_none = accept_none

    def __call__(self, x):
        if x is None:
            if self.accept_none:
                return True
            else:
                return False, 'is None'
        else:
            # truthy values does not work if threshold is 0
            # so we need to explicitly check for none
            if (self.low is not None) and self.low > x:
                return False, 'below threshold'
            if (self.high is not None) and self.high < x:
                return False, 'above threshold'
        return True

class Record(object):
    def __init__(self, doc):
        self.doc = doc

    def filter(self, **bounds):
        for key, bound in bounds.items():
            value = getattr(self, key)()
            # store filter values in metadata
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
