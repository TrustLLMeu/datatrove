from warc_with_meta import WarcReader
from html_extractor import HTMLExtractor, HTMLFilter
from signals import PreFilter, RepetitionFilter
from c4 import C4QualityFilter
from datatrove.io import DataFolder
from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.dedup import MinhashDedupCluster, MinhashDedupFilter, MinhashDedupSignature
from datatrove.pipeline.writers.jsonl import JsonlWriter
from datatrove.pipeline.filters import (
    LanguageFilter,
    URLFilter,
)

path = '/home/amaru/cc/data'

LANGSET = [
    'eng', # English
    'ang', # Old English
    'sco', # Scots
    'deu', # German
    'gsw', # Swiss German
    'swg', # Swabian
    'ksh', # Kölsch
    'nds', # Low German
    'bar', # Bavarian
    'stq', # Saterfriesisch
    'gos', # Gronings
    'hrx', # Hunsrik
    'pdc', # Pennsylvania German
    'pfl', # Pfaelzisch
    'prg', # Prussian
    'got', # Gothic
    'gmh', # Middle High German
    'nld', # Dutch
    'afr', # Afrikaans
    'fry', # Western Frisian
    'frr', # Northern Frisian
    'ltz', # Luxembourgish
    'vls', # Vlaams
    'lim', # Limburgish
    'zea', # Zeelandic
    'swe', # Swedish
    'dan', # Danish
    'nno', # Norwegian (Nynorsk)
    'nob', # Norwegian (Bokmål)
    'isl', # Icelandic
    'fao', # Faroese
    'non', # Old Norse
    ]

pipeline = [
        WarcReader(
            DataFolder(path),
            min_length=512,
            ),
        URLFilter(exclusion_writer=JsonlWriter(f'removed/url')),
        HTMLFilter(), #This is not a filter, it just adds html metadata tags that are removed by text extraction.
        HTMLExtractor(),
        PreFilter(exclusion_writer=JsonlWriter(f'removed/prefilter')),
        LanguageFilter(
            exclusion_writer=JsonlWriter(f'removed/language'),
            languages = [f'{l}_Latn' for l in LANGSET],
            backend='glotlid',
            language_threshold=.4
            ),
        RepetitionFilter(exclusion_writer=JsonlWriter(f'removed/repetition')),
        C4QualityFilter(
            filter_no_terminal_punct=False,
            filter_curly_bracket=False,
            filter_javascript=False,
            exclusion_writer=JsonlWriter('removed/c4')
            ),
        JsonlWriter('out'),
        ]

executor = LocalPipelineExecutor(
    pipeline=pipeline,
    logging_dir="logs/",
    tasks=3,
    workers=5
)

if __name__ == '__main__':
    executor.run()
