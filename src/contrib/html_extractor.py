from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.extractors.base import BaseExtractor
from datatrove.data import Document
import unicodedata

def maybe_update(dict, key, val):
    if val is not None:
        dict[key] = val

class HTMLFilter(BaseFilter):
    """
    Extracts html metadata
    """

    name = "📋 HTML Filter"

    _requires_dependencies = ["resiliparse"]

    def __init__(
            self,
            ):
        super().__init__()
        from resiliparse.parse.html import HTMLTree
        self.parser = HTMLTree

    def filter(self, doc: Document):
        html = self.parser.parse(doc.text)

        metas = {name: None for name in [
            'tdm-policy', 
            'tdm-reservation', 
            'keywords', 
            'description',
            ]}
        
        if html.head is not None:
            for match in html.head.query_selector_all(
                    ','.join(f'meta[name={name}]' for name in metas)
                    ):
                metas[match.getattr('name')] = match.getattr('content')
        
        # overwrite tdm headers IFF tdm is present in the meta tags
        maybe_update(doc.metadata, 'tdm_policy', metas['tdm-policy'])
        maybe_update(doc.metadata, 'tdm_reservation', metas['tdm-reservation'])
        
        # add html-metadata
        for name in metas:
            if name in ['tdm-policy', 'tdm-reservation']:
                continue
            doc.metadata[name] = metas[name]
        return True

class HTMLExtractor(BaseExtractor):
    """
    Extracts main content and tdm-relevant
    """

    name = "⚙️  HTML Extractor"
    # Resiliparse is much much faster than trafilatura, and produces nice formatting.
    _requires_dependencies = ["resiliparse"]

    def __init__(
        self,
        min_length=128,
        timeout = 0.2,
    ):
        super().__init__(timeout)
        from resiliparse.extract.html2text import extract_plain_text

        self.extract = lambda html: unicodedata.normalize('NFC', extract_plain_text(html, main_content=True, preserve_formatting=True))

    def extract(self, doc: str) -> str:
        return self.extract(doc)
