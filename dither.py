
# credits to https://www.emexee.com/2022/01/thermal-printer-image-converter.html
# https://github.com/LynMoe/DingdangD1-PoC/blob/main/app.py#L12
# using floyd-steinberg dithering
def applyDither(size, pixels, brightness, contrast):
    def getValue(pixels, y, x):
        return int((pixels[x, y][0] + pixels[x, y][1] + pixels[x, y][2]) / 3)
    def setValue(pixels, y, x, v):
        pixels[x, y] = (v, v, v)
    def nudgeValue(pixels, y, x, v):
        v = int(v)
        pixels[x, y] = (pixels[x, y][0] + v, pixels[x, y][1] + v, pixels[x, y][2] + v)
    w, h = size
    for y in range(h):
        for x in range(w):
            for i in range(3):
                r, g, b = pixels[x, y]
                arr = [r, g, b]
                arr[i] += (brightness - 0.5) * 256
                arr[i] = (arr[i] - 128) * contrast + 128
                arr[i] = int(min(max(arr[i], 0), 255))
                pixels[x, y] = (arr[0], arr[1], arr[2])

    for y in range(h):
        BOTTOM_ROW = y == h - 1
        for x in range(w):
            LEFT_EDGE = x == 0
            RIGHT_EDGE = x == w - 1
            i = (y * w + x) * 4
            level = getValue(pixels, y, x)
            newLevel = (level < 128) * 0 + (level >= 128) * 255
            setValue(pixels, y, x, newLevel)
            error = level - newLevel
            if not RIGHT_EDGE:
                nudgeValue(pixels, y, x + 1, error * 7 / 16)
            if not BOTTOM_ROW and not LEFT_EDGE:
                nudgeValue(pixels, y + 1, x - 1, error * 3 / 16)
            if not BOTTOM_ROW:
                nudgeValue(pixels, y + 1, x, error * 5 / 16)
            if not BOTTOM_ROW and not RIGHT_EDGE:
                nudgeValue(pixels, y + 1, x + 1, error * 1 / 16)
    result = ""
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b = pixels[x, y]
            if r + g + b > 600:
                result += '0'
            else:
                result += '1'
    # start bits
    result = '1' + '0' * 318 + result
    # convert to hex
    return hex(int(result, 2))[2:]

