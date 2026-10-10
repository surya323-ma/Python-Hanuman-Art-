# Python Hanuman Art 🚩💻

Automated digital-art generator built with Python and OpenCV. The program splits an image into colour regions using K-Means, traces each region's border with a live cursor, and fills the colour part by part, like watching an artist paint. Canny edges add the final crisp ink lines.

---

## ✨ Features

- **Sequential part drawing:** outlines and fills region by region (mukut, face, clothes, garland, details), biggest parts first.
- **Live cursor simulation:** a pointer follows the outline and glides between parts.
- **Top-to-bottom fill sweep:** each region is painted in bands instead of appearing instantly.
- **Auto screen fit:** image is scaled to a fixed height (default 700 px) so it fits above the taskbar.
- **Repeatable output:** K-Means is seeded, so every run looks the same.
- **Record & export:** save the animation as an MP4 and the result as a PNG.
- **Keyboard controls:** pause, turbo mode, quit.
- **Pure Python + OpenCV:** only `opencv-python` and `numpy`.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/python-hanuman-art.git
cd python-hanuman-art
```

### 2. Install dependencies
```bash
pip install opencv-python numpy
```

### 3. Run
Keep `animehanumanji.jpg` in the same folder as the script, then:
```bash
python animehanumanji.py
```

---

## ⚙️ Options

```bash
python animehanumanji.py [image] [options]
```

| Option | Default | Description |
|---|---|---|
| `image` | `animehanumanji.jpg` | Path to the input image |
| `--segments` | `18` | Number of K-Means colour clusters |
| `--height` | `700` | Working image height in px |
| `--min-area` | `120` | Ignore regions smaller than this (noise filter) |
| `--step` | `3` | Contour point skip; higher means faster tracing |
| `--fill-steps` | `6` | Number of bands in the fill sweep |
| `--speed` | `1.0` | Animation speed multiplier |
| `--flat` | off | Fill with flat cluster colours for a cartoon look |
| `--seed` | `42` | K-Means seed for repeatable results |
| `--record OUT.mp4` | none | Record the animation to a video |
| `--save OUT.png` | none | Save the final image |

**Examples**
```bash
# Faster, flat cartoon colours
python animehanumanji.py --speed 3 --flat

# Record a video and save the final picture
python animehanumanji.py --record hanuman.mp4 --save hanuman_final.png

# More detail
python animehanumanji.py --segments 24 --min-area 60
```

---

## 🎮 Controls

| Key | Action |
|---|---|
| `ESC` | Quit |
| `SPACE` | Pause / resume |
| `S` | Toggle turbo mode |

---

## 🧠 How it works

1. **Resize** the image to a fixed height, keeping the aspect ratio.
2. **Edges:** bilateral filter followed by Canny gives the final ink outline.
3. **Segmentation:** K-Means groups pixels into colour clusters; connected components turn each cluster into separate parts.
4. **Ordering:** parts are sorted by area, so large bases come first and small details (tilak, beads) come last.
5. **Animation loop** for every part: trace the outline, glide to the centre, fill the colour.
6. **Final touch:** Canny edges are overlaid on the finished canvas.

---

## 🛠️ Tech Stack

Python 3 · OpenCV · NumPy

---

## 📄 License

MIT. Feel free to use and modify.

*Jai Shri Ram, Jai Hanuman* 🙏
