from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.data import Document

def maybe_update(dict, key, val):
    if val is not None:
        dict[key] = val


class HTMLMetadata(BaseFilter):
    """
    Appends metadata to the thml document.
    Does not filter, but datatrove has strange
    interfaces ...
    """

    name = "📋 HTML Metadata"
    _requires_dependencies = ["resiliparse"]

    def __init__(
        self,
    ):
        from resiliparse.parse.html import HTMLTree

        self.parser = HTMLTree

        super().__init__()

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        html = self.parser.parse(doc.text)
        metas = {name: None for name in ['tdm-policy', 'tdm-reservation', 'keywords', 'description']}
        
        if html.head is not None:
            for match in html.head.query_selector_all(
                    ','.join(f'meta[name={name}]' for name in metas)
                    ):
                metas[match.getattr('name')] = match.getattr('content')
        
        # overwrite tdm headers IFF tdm is present in the meta tags
        maybe_update(doc.metadata, 'tdm_policy', metas['tdm-policy'])
        maybe_update(doc.metadata, 'tdm_reservation', metas['tdm-reservation'])
        
        # add html-metadata
        doc.metadata['keywords'] = metas['keywords']
        doc.metadata['description'] = metas['description']
        
        return True
