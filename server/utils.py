import stat
import os
import time
import stat

"""
    UNIX system only
"""


def get_file_properties(file_path):

    _stat = os.stat(file_path)
    message = []

    def _get_file_mode():

        modes = [
            stat.S_IRUSR,  # ~ Owner has read permission.
            stat.S_IWUSR,  # ~ Owner has write permission.
            stat.S_IXUSR,  # ~ Owner has execute permission.
            stat.S_IRGRP,  # ~ Group has read permission.
            stat.S_IWGRP,  # ~ Group has write permission
            stat.S_IXGRP,  # ~ Group has execute permission.
            stat.S_IROTH,  # ~ Others have read permission.
            stat.S_IWOTH,  # ~ Others have write permission.
            stat.S_IXOTH,  # ~ Others have execute permission.
        ]

    def _get_size():
        return str(_stat.st_size)

    def _get_last_time():
        return time.strftime("%b %d %H:%M", time.gmtime(_stat.st_mtime))

    for function in ("_get_size()", "_get_last_time()"):
        print(eval(function))
        message.append(eval(function))

    # ^Add file name
    message.append(os.path.basename(file_path))

    print(message)
    return " ".join(message)
