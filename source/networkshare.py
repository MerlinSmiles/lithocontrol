from contextlib import contextmanager
import os

@contextmanager
def network_share_auth(share, username='nanouser', password='zep520', drive_letter='P'):
    """Context manager that mounts the given share using the given
    username and password to the given drive letter when entering
    the context and unmounts it when exiting."""
    cmd_parts = ["NET USE %s: %s" % (drive_letter, share)]
    if password:
        cmd_parts.append(password)
    if username:
        cmd_parts.append("/USER:%s" % username)
    os.system(" ".join(cmd_parts))
    try:
        yield
    finally:
        os.system("NET USE %s: /DELETE" % drive_letter)
