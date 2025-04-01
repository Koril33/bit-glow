from PIL import Image


def resize_image(img, base_width):
    width_percent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(width_percent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    return img


def binaries(img, threshold, invert=False):
    # Grayscale
    img_gray = img.convert('L')
    img_gray = img_gray.point(lambda p: 255 if p > threshold else 0)

    # Invert colors if needed
    if invert:
        img_gray = img_gray.point(lambda p: 255 - p)

    # To mono
    res_img = img_gray.convert('1')
    return res_img

def to_array(img):
    width, height = img.size
    pixels = list(img.getdata())

    bit_map = []
    for y in range(0, height, 8):  # 每次处理 8 行
        for x in range(width):
            byte = 0
            for bit in range(8):
                if y + bit < height and pixels[(y + bit) * width + x] == 0:  # 黑色像素
                    byte |= (1 << bit)
            bit_map.append(byte)
    return {
        'width': width,
        'height': height,
        'bit_map': bit_map,
    }

def get_c_array_str(bit_map_info):
    width = bit_map_info['width']
    height = bit_map_info['height']
    bit_map = bit_map_info['bit_map']

    size_info = f'_{width}x{height}'

    c_array = "const unsigned char bit_map" + size_info + "[] = {\n"
    c_array += ", ".join(f"0x{b:02X}" for b in bit_map)
    c_array += "\n};"

    return c_array

def main():
    img = Image.open('./test_img/1.jpg')
    print(f'{img.format} - {img.size} - {img.mode}')
    img = resize_image(img, base_width=64)
    res = binaries(img, threshold=200, invert=True)
    res.show()
    bit_map = to_array(res)
    print(bit_map)
    c_array = get_c_array_str(bit_map)
    print(c_array)


if __name__ == '__main__':
    main()