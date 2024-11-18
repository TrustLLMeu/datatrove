from warc_with_meta import WarcReader
from html_metadata import HTMLMetadata
from datatrove.io import DataFolder
from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.writers.jsonl import JsonlWriter


pipeline = [
        WarcReader(
            DataFolder('path/to/cc-folder')
            ),
        HTMLMetadata(),
        JsonlWriter('out')
        ]

executor = LocalPipelineExecutor(
    pipeline=pipeline,
    logging_dir="logs/",
    tasks=10,
    workers=5
)

if __name__ == '__main__':
    executor.run()
