from __future__ import annotations

from typing import IO, TYPE_CHECKING, override

from django.conf import settings
from django.core.files.uploadhandler import StopUpload, TemporaryFileUploadHandler

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile
    from django.http.request import QueryDict
    from django.utils.datastructures import MultiValueDict


class MaxFileSizeTemporaryFileUploadHandler(TemporaryFileUploadHandler):
    @override
    def handle_raw_input(
        self,
        input_data: IO[bytes],
        META: dict[str, str],
        content_length: int,
        boundary: str,
        encoding: str | None = None,
    ) -> tuple[QueryDict, MultiValueDict[str, UploadedFile]] | None:
        """
        Use the content_length to enforce max size limit.
        """
        # Check the content-length header to see if we should
        # If the post is too large, we cannot use the Memory handler.
        if content_length > settings.FILE_UPLOAD_MAX_FILE_SIZE:
            raise StopUpload
