from PIL import Image, ImageSequence


def resize_image(img, base_width):
    """
    根据给定宽度，等比缩放图片
    :param img: PIL image
    :param base_width: 给定的宽度
    :return: 缩放后的 PIL image
    """
    width_percent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(width_percent)))
    return img.resize((base_width, hsize), Image.Resampling.LANCZOS)


def binaries(img, threshold, invert=False):
    """
    将图片转成 0 和 1 组成的数组
    :param img: PIL image
    :param threshold: 阈值
    :param invert: 反色
    :return: 返回图片以及宽和高
    """
    # Grayscale
    img_gray = img.convert('L')
    v = 255 if not invert else 0
    img_gray = img_gray.point(lambda p: v if p > threshold else abs(v-255))

    # 预览灰度图
    # img_gray.show()

    img_gray_data = list(img_gray.getdata())

    res = [1 if v == 255 else 0 for v in img_gray_data]
    return {
        'width': img.size[0],
        'height': img.size[1],
        'bit_map': res
    }


def get_c_array_str(bit_map_info):
    """
    转成 C 数组格式
    :param bit_map_info: 经过 binary 函数得到的对象
    :return: C 数组格式的字符串
    """

    width = bit_map_info['width']
    height = bit_map_info['height']
    bit_map = bit_map_info['bit_map']

    size_info = f'_{width}x{height}'

    byte_array = []
    # 每 8 个元素组成一个字节
    for i in range(0, len(bit_map), 8):
        chunk = bit_map[i:i+8]
        byte_value = 0
        for bit in chunk:
            byte_value = (byte_value << 1) | bit
        byte_array.append(byte_value)

    # 转换成 C 数组的字符串形式
    c_array = "const unsigned char bit_map" + size_info + "[] = {\n  "
    c_array += ", ".join(f"0x{b:02X}" for b in byte_array)
    c_array += "\n};\n"

    return c_array

def get_c_array_str_by_gif(frames_bitmaps_info):
    """
    将 GIF 每一帧的位图数据转换为 C 语言二维数组格式
    :param frames_bitmaps_info: [[0, 0, 1...], [1, 1, 1...]] (每一帧的二值化位图) 以及宽高信息
    :return: C 语言二维数组字符串
    """
    width = frames_bitmaps_info['width']
    height = frames_bitmaps_info['height']
    frames_bitmaps = frames_bitmaps_info['bit_map']
    
    size_info = f'_{width}x{height}'
    frame_count = len(frames_bitmaps)

    c_array = f"const unsigned char bit_map{size_info}[{frame_count}][] = {{\n"

    for frame_index, bit_map in enumerate(frames_bitmaps):
        byte_array = []
        for i in range(0, len(bit_map), 8):
            chunk = bit_map[i:i+8]
            byte_value = sum(bit << (7 - j) for j, bit in enumerate(chunk))
            byte_array.append(byte_value)

        # 添加到 C 数组，每一帧一行
        c_array += f"  {{ {', '.join(f'0x{b:02X}' for b in byte_array)} }},\n"

    c_array += "};\n"
    return c_array

def process_image(img, base_width=64, threshold=180):
    """ 处理图片，支持 GIF 动图 """
    print(f"{img.format} - {img.size} - {img.mode}")
    c_array = None
    if img.format == "GIF":
        res = {
            'width': None,
            'height': None,
            'bit_map': None
        }
        bit_maps = []
        # 处理 GIF 每一帧
        for frame_index, frame in enumerate(ImageSequence.Iterator(img)):
            frame = resize_image(frame.convert("RGB"), base_width)
            bit_map_info = binaries(frame, threshold, False)
            if not res.get('width'):
                res['width'] = bit_map_info['width']
            if not res.get('height'):
                res['height'] = bit_map_info['height']
            bit_maps.append(bit_map_info['bit_map'])
        res.update({'bit_map': bit_maps})
        c_array = get_c_array_str_by_gif(res)
    else:
        # 处理普通图片
        img = resize_image(img, base_width)
        res = binaries(img, threshold)
        c_array = get_c_array_str(res)

    return c_array

def main():
    # img = Image.open('./test_img/9.jpg')
    img = Image.open('./test_gif/1.gif')

    # print(f'{img.format} - {img.size} - {img.mode}')
    # img = resize_image(img, base_width=64)
    # res = binaries(img, threshold=180, invert=True)
    # c_array = get_c_array_str(res)
    # print(c_array)

    print(process_image(img, threshold=100))

if __name__ == '__main__':
    main()