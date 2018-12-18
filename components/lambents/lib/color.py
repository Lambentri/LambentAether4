import colorsys


class HSVHelper(object):

    def _sys_255_to_1(self, values):
        return [i / 255.0 for i in values]

    def _sys_1_to_255(self, values):
        return [i * 255 for i in values]

    def _hsv_to_rgb(self, h, s, v):
        h_, s_, v_ = self._sys_255_to_1([h, s, v])
        r_, g_, b_ = colorsys.hsv_to_rgb(h_, s_, v_)
        r, g, b = self._sys_1_to_255([r_, g_, b_])
        return r, g, b

    def _rgb_to_hsv(self, r, g, b):
        r_, g_, b_ = self._sys_255_to_1([r, g, b])
        h_, s_, v_ = colorsys.rgb_to_hsv(r_, g_, b_)
        h, s, v = self._sys_1_to_255([h_, s_, v_])
        return h, s, v

    def read(self):
        return [self.h, self.s, self.v]

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h, self.s, self.v)
        return [int(r), int(g), int(b)]

    def read_t(self):
        return [self.h_t, self.s_t, self.v_t]

    def read_t_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h_t, self.s_t, self.v_t)
        return [r, g, b]


class HSVHelperFull(HSVHelper):
    def __init__(self,h,s,v):
        self.h = h
        self.s = s
        self.v = v

        self.h_t = h
        self.s_t = s
        self.v_t = v


