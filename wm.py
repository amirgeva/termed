from typing import List
from geom import Rect, Point
from window import Window


class WindowManager:
    windows: List[Window]

    def __init__(self, rect: Rect):
        self.rect = rect
        self.windows = []  # type: List[Window]

    def add_window(self, w: Window):
        try:
            _ = self.windows.index(w)
        except ValueError:
            if w.requested_size().x > 0:
                self.windows.insert(1, w)
            else:
                self.windows.append(w)
            self.reorg()

    def remove_window(self, w: Window):
        try:
            i = self.windows.index(w)
            del self.windows[i]
            self.reorg()
        except ValueError:
            pass

    def reorg(self):
        r0 = Rect(self.rect)
        rects = [r0]
        x = r0.pos.x + r0.width()
        y = r0.pos.y + r0.height()
        bottom_index = -1
        for i in range(1, len(self.windows)):
            w = self.windows[i]
            req = w.requested_size()
            if req.x > 0:
                rects.append(Rect(x, 0, req.x, r0.height()))
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
        for i in range(1, bottom_index):
            rects[i].move(Point(-reduction, 0))
        if bottom_index > 0:
            height = rects[-1].bottom()
            reduction = height - self.rect.height()
            for i in range(bottom_index):
                rects[i].size.y -= reduction
            for i in range(bottom_index, len(rects)):
                rects[i].move(Point(0, -reduction))
        for i in range(len(rects)):
            self.windows[i].set_rect(rects[i])
