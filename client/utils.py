from typing import List, Union
import os
import stat
import time
from PyQt5 import QtGui
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItemIterator
from PyQt5 import sip


class HumanSize:
    METRIC_LABELS: List[str] = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    BINARY_LABELS: List[str] = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    PRECISION_OFFSETS: List[float] = [0.5, 0.05, 0.005, 0.0005]  # PREDEFINED FOR SPEED.
    PRECISION_FORMATS: List[str] = ["{}{:.0f} {}", "{}{:.1f} {}", "{}{:.2f} {}", "{}{:.3f} {}"]  # PREDEFINED FOR SPEED.

    @staticmethod
    def format(num: Union[int, float], metric: bool = False, precision: int = 1) -> str:
        """
        Human-readable formatting of bytes, using binary (powers of 1024)
        or metric (powers of 1000) representation.
        """

        assert isinstance(num, (int, float)), "num must be an int or float"
        assert isinstance(metric, bool), "metric must be a bool"
        assert isinstance(precision, int) and 0 <= precision <= 3, "precision must be an int (range 0-3)"

        unit_labels = HumanSize.METRIC_LABELS if metric else HumanSize.BINARY_LABELS
        last_label = unit_labels[-1]
        unit_step = 1000 if metric else 1024
        unit_step_thresh = unit_step - HumanSize.PRECISION_OFFSETS[precision]

        is_negative = num < 0
        if is_negative:  # Faster than ternary assignment or always running abs().
            num = abs(num)

        for unit in unit_labels:
            if num < unit_step_thresh:
                # VERY IMPORTANT:
                # Only accepts the CURRENT unit if we're BELOW the threshold where
                # float rounding behavior would place us into the NEXT unit: F.ex.
                # when rounding a float to 1 decimal, any number ">= 1023.95" will
                # be rounded to "1024.0". Obviously we don't want ugly output such
                # as "1024.0 KiB", since the proper term for that is "1.0 MiB".
                break
            if unit != last_label:
                # We only shrink the number if we HAVEN'T reached the last unit.
                # NOTE: These looped divisions accumulate floating point rounding
                # errors, but each new division pushes the rounding errors further
                # and further down in the decimals, so it doesn't matter at all.
                num /= unit_step

        return HumanSize.PRECISION_FORMATS[precision].format("-" if is_negative else "", num, unit)


def parse_file_info(info: str):
    item = [i for i in info.split(" ") if i != ""]

    modes, size, date, name = (item[0], item[1], ' '.join(item[2:4]), item[5:])

    name = " ".join(name)
    size = HumanSize.format(int(size), precision=2)

    return modes, size, date, name


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

        mode = _stat.st_mode
        full_mode = ""
        full_mode += "d" if os.path.isdir(file_path) else "-"

        for i in range(9):
            full_mode += bool(mode & modes[i]) and 'rwxrwxrwx'[i] or '-'
        return full_mode

    def _get_size():
        return str(_stat.st_size)

    def _get_last_time():
        return time.strftime("%b %d %H:%M", time.gmtime(_stat.st_mtime))

    for function in ("_get_file_mode()", "_get_size()", "_get_last_time()"):
        message.append(eval(function))

    # ^Add file name
    message.append(os.path.basename(file_path))

    return " ".join(message)


def path_parser(path: str):
    return path if path.endswith(os.path.sep) else path + os.path.sep


def clearQTreeWidget(tree: QTreeWidget):
    # iterator = QtGui.QTreeWidgetItemIterator(tree, QtGui.QTreeWidgetItemIterator.All)
    # while iterator.value():
    #     iterator.value().takeChildren()
    #     iterator +=1
    # i = tree.topLevelItemCount()
    # while i > -1:
    #     tree.takeTopLevelItem(i)
    #     i -= 1
    a = QTreeWidgetItemIterator(tree)
    root = tree.invisibleRootItem()
    while a.value():
        item = a.value()
        sip.delete(item)
        a += 1
    i = tree.topLevelItemCount()
    while i > -1:
        tree.takeTopLevelItem(i)
        i -= 1