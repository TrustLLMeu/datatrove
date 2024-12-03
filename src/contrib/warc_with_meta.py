from typing import TYPE_CHECKING, Callable, Literal

from datatrove.io import DataFileLike, DataFolderLike
from datatrove.pipeline.readers.base import BaseDiskReader


#if TYPE_CHECKING:
#    from warcio.recordloader import ArcWarcRecord


class WarcReader(BaseDiskReader):
    """Read data from WARC files.
        Will read each record as a separate document.

    Args:
        data_folder: a str, tuple or DataFolder object representing a path/filesystem
        paths_file: optionally provide a file with one path per line (without the `data_folder` prefix) to read.
        compression: the compression to use (default: "infer")
        limit: limit the number of documents to read. Useful for debugging
        skip: skip the first n rows
        file_progress: show progress bar for files
        doc_progress: show progress bar for documents
        adapter: function to adapt the data dict from the source to a Document.
            Takes as input: (self, data: dict, path: str, id_in_file: int | str)
                self allows access to self.text_key and self.id_key
            Returns: a dict with at least a "text" and "id" keys
        text_key: the key containing the text data (default: "text").
        id_key: the key containing the id for each sample (default: "id").
        default_metadata: a dictionary with any data that should be added to all samples' metadata
        recursive: whether to search files recursively. Ignored if paths_file is provided
        glob_pattern: pattern that all files must match exactly to be included (relative to data_folder). Ignored if paths_file is provided
        shuffle_files: shuffle the files within the returned shard. Mostly used for data viz. purposes, do not use with dedup blocks
    """

    name = "🕷 Warc + TDM"
    _requires_dependencies = ["fastwarc", ("cchardet", "faust-cchardet"), ("magic", "python-magic")]

    def __init__(
        self,
        data_folder: DataFolderLike,
        paths_file: DataFileLike | None = None,
        compression: Literal["infer", "gzip", "zstd"] | None = "infer",
        limit: int = -1,
        skip: int = 0,
        file_progress: bool = False,
        doc_progress: bool = False,
        adapter: Callable = None,
        text_key: str = "text",
        id_key: str = "id",
        default_metadata: dict = None,
        min_length = 0,
        recursive: bool = True,
        glob_pattern: str | None = None,
        shuffle_files: bool = False,
    ):
        self.compression = compression
        super().__init__(
            data_folder,
            paths_file,
            limit,
            skip,
            file_progress,
            doc_progress,
            adapter,
            text_key,
            id_key,
            default_metadata,
            recursive,
            glob_pattern,
            shuffle_files,
        )
        self.min_length=min_length

    def read_file(self, filepath: str):
        from fastwarc.warc import ArchiveIterator, WarcRecordType, WarcRecord


        with self.data_folder.open(filepath, "rb", compression=self.compression) as f:
            for ri, record in enumerate(ArchiveIterator(
                    f,
                    record_types=WarcRecordType.response,
                    min_content_length=self.min_length
                    )):
                with self.track_time():
                    extracted_data = process_record(record)
                    if not extracted_data:
                        continue
                    document = self.get_document_from_dict(extracted_data, filepath, ri)
                    if not document:
                        continue
                yield document


def process_record(record : "WarcRecord") -> dict | None:
    """Process a WARC record to extract the html and metadata (id, url, date)."""
    import cchardet
    import magic

    # record type
    #if record.rec_type != "response" and record.rec_type != "conversion":  # wet files have "conversion" type
    #    return


    # content type filtering
    mime_type = record.headers.get("WARC-Identified-Payload-Type", None)
    if mime_type is not None and mime_type != "text/html":
        return

    record.parse_http()
    content_bytes = record.reader.read()
    if mime_type is None:
        # fallback for older crawls without payload types
        mime_type = magic.from_buffer(content_bytes, mime=True)
        if mime_type != "text/html":
            return

    # Decode the response bytes
    charset = "UTF-8"
    try:
        html = content_bytes.decode(charset)
    except UnicodeDecodeError:
        encoding_det = cchardet.detect(content_bytes)["encoding"]
        if not encoding_det or encoding_det == charset:
            return
        charset = encoding_det

        try:
            html = content_bytes.decode(charset)
        except (UnicodeDecodeError, LookupError):
            return

    id_ = record.headers["WARC-Record-ID"]
    url = record.headers.get("WARC-Target-URI", None)
    date = record.headers.get("WARC-Date", None)
    offset = record.stream_pos
    charset = charset
    tdm_reservation = record.http_headers.get('tdm-reservation', None)
    tdm_policy = record.http_headers.get('tdm-policy', None)

    # handle older formats
    if not url:
        url = record.headers["uri"]
    if not date:
        date = record.headers["archive-date"]

    return {"text": html, "id": id_, "offset": offset, "original_charset": charset, "url": url, "date": date, "tdm_reservation": tdm_reservation, "tdm_policy": tdm_policy}
