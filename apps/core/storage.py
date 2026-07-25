from django.conf import settings
from django.core.files.storage import FileSystemStorage


class SafeMediaStorage(FileSystemStorage):
    """Media storage with explicit paths and non-executable file permissions."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.MEDIA_ROOT)
        kwargs.setdefault('base_url', settings.MEDIA_URL)
        kwargs.setdefault('file_permissions_mode', settings.FILE_UPLOAD_PERMISSIONS)
        kwargs.setdefault(
            'directory_permissions_mode',
            settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS,
        )
        super().__init__(*args, **kwargs)
