import re
import sys
import os
from pathlib import Path


def _read_ppm_text(text, path):
    if text.startswith('\ufeff'):
        text = text[1:]
    text = text.replace('\r', '\n')
    tokens = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '#' in line:
            line = line.split('#', 1)[0].strip()
        if not line:
            continue
        tokens.extend(line.split())

    if not tokens or tokens[0] != 'P3':
        raise ValueError(f'Unsupported PPM text format in {path}')
    if len(tokens) < 4:
        raise ValueError('PPM header is incomplete')

    width = int(tokens[1])
    height = int(tokens[2])
    maxval = int(tokens[3])
    expected = width * height * 3
    values = [int(tok) for tok in tokens[4:4 + expected]]
    if len(values) < expected:
        raise ValueError('PPM data is too short')
    return width, height, maxval, bytes(values)


def read_ppm(path):
    with open(path, 'rb') as f:
        start = f.read(4)
        if start.startswith(b'\xef\xbb\xbf'):
            raw = start[3:] + f.read()
            text = raw.decode('utf-8', errors='replace')
            return _read_ppm_text(text, path)
        if start.startswith(b'\xff\xfe') or start.startswith(b'\xfe\xff'):
            f.seek(0)
            raw = f.read()
            encoding = 'utf-16-le' if raw.startswith(b'\xff\xfe') else 'utf-16-be'
            text = raw.decode(encoding, errors='replace')
            return _read_ppm_text(text, path)

        f.seek(0)
        header = f.readline().strip()
        if header == b'P3':
            text = f.read().decode('ascii', errors='replace')
            return _read_ppm_text('P3\n' + text, path)
        if header == b'P6':
            token_bytes = b''
            while len(token_bytes.split()) < 3:
                line = f.readline()
                if not line:
                    raise EOFError('Unexpected end of file while reading header')
                line = line.strip()
                if not line or line.startswith(b'#'):
                    continue
                token_bytes += b' ' + line
            tokens = token_bytes.split()
            width = int(tokens[0])
            height = int(tokens[1])
            maxval = int(tokens[2])
            expected = width * height * 3
            pixels = f.read(expected)
            if len(pixels) < expected:
                raise ValueError('PPM binary data is too short')
            return width, height, maxval, pixels

        raise ValueError(f'Unsupported PPM format: {header!r}')


def show_ppm(path):
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        Image = None
        np = None

    width, height, maxval, data = read_ppm(path)

    if Image is not None and np is not None:
        array = np.frombuffer(data, dtype=np.uint8)
        array = array.reshape((height, width, 3))
        img = Image.fromarray(array, 'RGB')
        img.show(title=Path(path).name)
        return

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        array = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        plt.imshow(array)
        plt.axis('off')
        plt.title(Path(path).name)
        plt.show()
        return
    except ImportError:
        pass

    try:
        import tkinter as tk
        root = tk.Tk()
        root.title(Path(path).name)
        photo = tk.PhotoImage(file=path)
        label = tk.Label(root, image=photo)
        label.image = photo
        label.pack()
        root.mainloop()
        return
    except Exception:
        pass

    try:
        import tkinter as tk
        from PIL import ImageTk
        if Image is None:
            raise ImportError
        root = tk.Tk()
        root.title(Path(path).name)
        array = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        img = Image.fromarray(array, 'RGB')
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=photo)
        label.image = photo
        label.pack()
        root.mainloop()
        return
    except Exception:
        pass

    print('Unable to display image automatically.')
    print(f'PPM file loaded: {path}')
    print(f'Width: {width}, Height: {height}, Maxval: {maxval}')
    print('You can install Pillow (pip install pillow) or matplotlib (pip install matplotlib) to view the image.')


def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print('Usage: py -m ppm_view path\to\image.ppm')
        sys.exit(1)

    if not os.path.isfile(path):
        print(f'File not found: {path}')
        sys.exit(1)

    show_ppm(path)


if __name__ == '__main__':
    main()

