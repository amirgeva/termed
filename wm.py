from typing import List, Optional
from geom import Rect, Point
from window import Window


class WindowManager:
    # _windows: List[Window]

    def __init__(self, rect: Rect):
        self.rect = rect
        self._windows_set = set()
        self._windows: List[Window] = []
        self._hidden_windows = set()

    def hide_window(self, w: Window):
        self._hidden_windows.add(w)
        self.reorg()

    def show_window(self, w: Window):
        self._hidden_windows.remove(w)
        self.reorg()

    def add_window(self, w: Window):
        if w not in self._windows_set:
            self._windows_set.add(w)
            if w.requested_size().x > 0:
                self._windows.insert(1, w)
            else:
                self._windows.append(w)
            self.reorg()

    def remove_window(self, w: Window):
        try:
            self._windows_set.remove(w)
            self._windows.remove(w)
            self.reorg()
        except KeyError:
            pass
        except ValueError:
            pass

    def reorg(self):
        r0 = Rect(self.rect)
        rects = [r0]
        x = r0.pos.x + r0.width()
        y = r0.pos.y + r0.height()
        bottom_index = -1
        windows = [w for w in self._windows if w not in self._hidden_windows]
        for i in range(1, len(windows)):
            w = windows[i]
            req = w.requested_size()
            if req.x > 0:
                rects.append(Rect(x, 1, req.x, r0.height()))
                x += req.x
            elif req.y > 0:
                if bottom_index < 0:
                    bottom_index = len(rects)
                rects.append(Rect(0, y, r0.width(), req.y))
                y += req.y
            else:
                raise RuntimeError("Invalid window size requirement")
        if bottom_index > 0:
            width = rects[bottom_index - 1].right()
        else:
            width = rects[-1].right()
        reduction = width - self.rect.width()
        rects[0].size.x -= reduction
        right_max = bottom_index if bottom_index > 0 else len(rects)
        for i in range(1, right_max):
            rects[i].move(Point(-reduction, 0))
        if bottom_index > 0:
            height = rects[-1].bottom()
            reduction = height - self.rect.height() - 1
            for i in range(bottom_index):
                rects[i].size.y -= reduction
            for i in range(bottom_index, len(rects)):
                rects[i].move(Point(0, -reduction))
        for i in range(len(rects)):
            windows[i].set_rect(rects[i])


manager: Optional[WindowManager] = None
