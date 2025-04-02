from PIL import Image

def resize_image(img, base_width):
    """
    根据给定宽度，等比缩放图片
    :param img: PIL image
    :param base_width: 给定的宽度
    :return: 缩放后的 PIL image
    """
    width_percent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(width_percent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    return img


def binaries(img, threshold):
    """
    将图片转成 0 和 1 组成的数组
    :param img: PIL image
    :param threshold: 阈值
    :return: 返回图片以及宽和高
    """
    # Grayscale
    img_gray = img.convert('L')
    img_gray = img_gray.point(lambda p: 255 if p > threshold else 0)

    # 预览灰度图
    img_gray.show()

    img_gray_data = list(img_gray.getdata())
    res = []
    for v in img_gray_data:
        if v == 255:
            res.append(1)
        else:
            res.append(0)
    width, height = img.size

    return {
        'width': width,
        'height': height,
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
    c_array += "\n};"

    return c_array

def main():
    img = Image.open('./test_img/8.jpg')
    print(f'{img.format} - {img.size} - {img.mode}')
    img = resize_image(img, base_width=64)
    res = binaries(img, threshold=180)
    c_array = get_c_array_str(res)
    print(c_array)


if __name__ == '__main__':
    main()