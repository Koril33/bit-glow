from PIL import Image, ImageSequence, ImageFont, ImageDraw


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


def generate_ascii_c_array(width=8, height=16, font_path="arial.ttf", threshold=128):
    try:
        font = ImageFont.truetype(font_path, height)
    except IOError:
        print("Font file not found! Using default font.")
        font = ImageFont.load_default()

    ascii_array = f"const unsigned char ascii_{width}x{height}[128][] = " + '{\n'
    for char_code in range(32, 128):  # ASCII 0x20 - 0x7F
        char = chr(char_code)
        img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), char, 255, font=font)
        if char_code == 65:
            img.show()
        bit_map_info = binaries(img, threshold)

        byte_array = []
        for i in range(0, len(bit_map_info['bit_map']), 8):
            chunk = bit_map_info['bit_map'][i:i + 8]
            byte_value = sum(bit << (7 - j) for j, bit in enumerate(chunk))
            byte_array.append(byte_value)

        ascii_array += f"  /* {char} */ {{ {', '.join(f'0x{b:02X}' for b in byte_array)} }},\n"

    ascii_array += "};\n"
    return ascii_array


def generate_chinese_c_array(chinese='你好', width=16, height=16, font_path="simhei.ttf", threshold=128):
    """
    生成 C 语言格式的 16x16 汉字点阵数据
    :param chinese: 需要转换的汉字字符串
    :param width: 字符宽度
    :param height: 字符高度
    :param font_path: 字体文件路径（需支持中文）
    :param threshold: 二值化阈值
    :return: C 语言数组字符串
    """
    try:
        font = ImageFont.truetype(font_path, height)
    except IOError:
        print("Font file not found! Using default font.")
        return ""

    chinese_array = f"const unsigned char chinese_{width}x{height}[{len(chinese)}][] = {{\n"

    for char in chinese:
        img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), char, 255, font=font)

        bit_map_info = binaries(img, threshold)

        byte_array = []
        for i in range(0, len(bit_map_info['bit_map']), 8):
            chunk = bit_map_info['bit_map'][i:i + 8]
            byte_value = sum(bit << (7 - j) for j, bit in enumerate(chunk))
            byte_array.append(byte_value)

        hex_values = ', '.join(f'0x{b:02X}' for b in byte_array)
        chinese_array += f'  /* {char} */ {{ {hex_values} }},\n'

    chinese_array += "};\n"
    return chinese_array



def hex_string_to_bitmap(hex_string, width, height):
    """
    解析 C 语言格式的 { 0x00, 0x00, ..., 0x00 } 为 width x height 位图数据
    :param hex_string: C 数组格式的 16 进制字符串，如 "{ 0x00, 0xFF, ... }"
    :param width: 位图的宽度（像素）
    :param height: 位图的高度（像素）
    :return: 二维数组表示的位图
    """
    hex_values = [int(x, 16) for x in hex_string.replace("{", "").replace("}", "").split(",") if x.strip()]

    # 计算每行需要多少字节
    bytes_per_row = width // 8
    if len(hex_values) != bytes_per_row * height:
        raise ValueError("Hex 数据长度和指定的 width, height 不匹配")

    # 解析成 width x height 的二进制位图
    bitmap = []
    for row in range(height):
        row_bits = []
        for byte_index in range(bytes_per_row):
            value = hex_values[row * bytes_per_row + byte_index]
            bits = [(value >> (7 - i)) & 1 for i in range(8)]  # 高位在前
            row_bits.extend(bits)
        bitmap.append(row_bits[:width])  # 确保不会超出 width
    return bitmap


def render_bitmap(bitmap, width, height, pixel_size=10):
    """
    将 width x height 的位图渲染为黑白图片
    :param bitmap: 由 0 和 1 组成的二维数组
    :param width: 位图的宽度
    :param height: 位图的高度
    :param pixel_size: 每个像素的大小（放大倍数）
    """
    img = Image.new("1", (width * pixel_size, height * pixel_size), 1)  # 1 表示黑白图（1-黑, 0-白）
    draw = ImageDraw.Draw(img)

    for y in range(height):
        for x in range(width):
            if bitmap[y][x] == 1:
                draw.rectangle(
                    [x * pixel_size, y * pixel_size, (x + 1) * pixel_size - 1, (y + 1) * pixel_size - 1],
                    fill=0
                )

    img.show()


def main():
    # img = Image.open('./test_img/9.jpg')
    # img = Image.open('./test_gif/1.gif')

    # print(f'{img.format} - {img.size} - {img.mode}')
    # img = resize_image(img, base_width=64)
    # res = binaries(img, threshold=180, invert=True)
    # c_array = get_c_array_str(res)
    # print(c_array)

    # print(process_image(img, threshold=100))
    width = 32
    height = 32
    font_path = 'C:\\Windows\\Fonts\\simsun.ttc'
    # c_array = generate_ascii_c_array(
    #     width=width, height=height,
    #     font_path=font_path,
    # )
    c_array = generate_chinese_c_array(chinese='东南西北中', width=width, height=height, font_path=font_path)
    print(c_array)

    bitmap = hex_string_to_bitmap(
        '{ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x80, 0x01, 0xFF, 0xFF, 0xC0, 0x01, 0x81, 0x80, 0xC0, 0x01, 0x81, 0x80, 0x80, 0x01, 0x81, 0x80, 0x80, 0x01, 0xFF, 0xFF, 0x80, 0x01, 0x81, 0x80, 0x80, 0x01, 0x81, 0x80, 0x80, 0x01, 0x81, 0x80, 0x80, 0x01, 0x81, 0x80, 0x80, 0x01, 0xFF, 0xFF, 0x80, 0x01, 0x86, 0x20, 0x80, 0x00, 0x06, 0x10, 0x00, 0x00, 0x0C, 0x08, 0x00, 0x00, 0x18, 0x04, 0x00, 0x00, 0x38, 0x03, 0x00, 0x00, 0xEC, 0x0D, 0xF0, 0x01, 0x8C, 0x0C, 0x7C, 0x06, 0x08, 0x08, 0x18, 0x30, 0x18, 0x08, 0x00, 0x00, 0x18, 0x0C, 0x00, 0x00, 0x18, 0x0C, 0x00, 0x00, 0x30, 0x0C, 0x00, 0x00, 0x30, 0x0C, 0x00, 0x00, 0x60, 0x0C, 0x00, 0x01, 0x80, 0x0C, 0x00, 0x02, 0x00, 0x0C, 0x00, 0x08, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00 }',
        width=width, height=height
    )
    render_bitmap(bitmap, width=width, height=height)


if __name__ == '__main__':
    main()