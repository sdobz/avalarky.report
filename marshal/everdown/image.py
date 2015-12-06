from PIL import Image


def scale_and_crop(im, size):
    (pw, ph) = im.size
    (nw, nh) = size

    pr = float(pw) / float(ph)
    nr = float(nw) / float(nh)

    if pr > nr:
        # photo aspect is wider than destination ratio
        tw = int(round(nh * pr))
        im = im.resize((tw, nh), Image.LANCZOS)
        l = int(round((tw - nw) / 2.0))
        return im.crop((l, 0, l + nw, nh))
    elif pr < nr:
        # photo aspect is taller than destination ratio
        th = int(round(nw / pr))
        im = im.resize((nw, th), Image.LANCZOS)
        t = int(round((th - nh) / 2.0))
        return im.crop((0, t, nw, t + nh))
    else:
        # photo aspect matches the destination ratio
        return im.resize(size, Image.LANCZOS)


def constrain_size(im, size):
    (w, h) = im.size

    scale = None

    if w > size[0]:
        scale = float(size[0]) / float(w)

    if h > size[1]:
        h_scale = float(size[1]) / float(h)

        if scale is None:
            scale = h_scale
        else:
            scale = min(scale, h_scale)

    if scale is not None:
        return im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    return im
