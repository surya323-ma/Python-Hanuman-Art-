"""
Python Hanuman Art
------------------
Sequential digital-art simulation using OpenCV:
  1. K-Means splits the image into colour regions
  2. Each region is outlined by a moving cursor
  3. The region is then filled with a top-to-bottom colour sweep
  4. Canny edges give the final crisp ink touch

Controls (while the window is focused):
  ESC    quit
  SPACE  pause / resume
  S      toggle turbo (renders fewer frames, finishes faster)
"""
import argparse
import os
import sys

import cv2
import numpy as np

INK = (30, 30, 30)
WIN_NAME = "Sequential Part Draw & Fill"


# --------------------------------------------------------------------------- #
# Cursor
# --------------------------------------------------------------------------- #
def draw_cursor(canvas, x, y):
    h, w, _ = canvas.shape
    x = int(np.clip(x, 0, w - 1))
    y = int(np.clip(y, 0, h - 1))
    pt1 = (x, y)
    pt2 = (min(w - 1, x + 16), min(h - 1, y + 16))
    pt3 = (min(w - 1, x + 5), min(h - 1, y + 20))
    shape = np.array([pt1, pt2, pt3])
    cv2.drawContours(canvas, [shape], 0, INK, -1)
    cv2.drawContours(canvas, [shape], 0, (255, 255, 255), 1)
    cv2.circle(canvas, pt1, 2, (0, 0, 255), -1)


# --------------------------------------------------------------------------- #
# Renderer: window, pause/turbo/quit handling, optional video recording
# --------------------------------------------------------------------------- #
class Renderer:
    def __init__(self, size, speed=1.0, record_path=None, fps=30):
        self.w, self.h = size
        self.delay = max(1, int(round(1 / max(speed, 0.1))))
        self.turbo = False
        self.counter = 0
        self.writer = None
        if record_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(record_path, fourcc, fps, size)
            if not self.writer.isOpened():
                print(f"Warning: could not open '{record_path}' for recording.")
                self.writer = None
        cv2.namedWindow(WIN_NAME, cv2.WINDOW_AUTOSIZE)

    def show(self, canvas, cursor=None, wait=None):
        """Returns False if the user asked to quit."""
        frame = canvas.copy() if cursor else canvas
        if cursor:
            draw_cursor(frame, *cursor)
        if self.writer:
            self.writer.write(frame)

        self.counter += 1
        if self.turbo and self.counter % 12 and wait is None:
            return True

        cv2.imshow(WIN_NAME, frame)
        key = cv2.waitKey(wait if wait is not None else self.delay) & 0xFF
        if key == 27:
            return False
        if key == ord("s"):
            self.turbo = not self.turbo
        if key == 32:  # pause until SPACE again (ESC still quits)
            while True:
                k = cv2.waitKey(50) & 0xFF
                if k == 32:
                    break
                if k == 27:
                    return False
        return True

    def close(self):
        if self.writer:
            self.writer.release()
        cv2.destroyAllWindows()


# --------------------------------------------------------------------------- #
# Image processing
# --------------------------------------------------------------------------- #
def load_image(path, target_height):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"'{path}' not found or unreadable!")
    oh, ow, _ = img.shape
    tw = int(target_height * (ow / oh))
    return cv2.resize(img, (tw, target_height), interpolation=cv2.INTER_AREA)


def segment(img, k, seed):
    """K-Means colour segmentation. Returns (labels HxW, flat-colour image)."""
    h, w, _ = img.shape
    data = np.float32(img).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    cv2.setRNGSeed(seed)  # same result on every run
    _, labels, centers = cv2.kmeans(
        data, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    flat = np.uint8(centers)[labels.flatten()].reshape((h, w, 3))
    return labels.reshape((h, w)), flat


def extract_parts(labels, k, min_area):
    parts = []
    for seg_id in range(k):
        mask = (labels == seg_id).astype(np.uint8)
        n, comp, stats, cents = cv2.connectedComponentsWithStats(mask)
        for c in range(1, n):
            area = stats[c, cv2.CC_STAT_AREA]
            if area > min_area:
                parts.append(
                    {
                        "area": int(area),
                        "center": (int(cents[c][0]), int(cents[c][1])),
                        "mask": (comp == c).astype(np.uint8) * 255,
                        "bbox": (
                            stats[c, cv2.CC_STAT_TOP],
                            stats[c, cv2.CC_STAT_HEIGHT],
                        ),
                    }
                )
    # Big regions first (background / skin / mukut), tiny details last
    parts.sort(key=lambda p: p["area"], reverse=True)
    return parts


# --------------------------------------------------------------------------- #
# Main animation
# --------------------------------------------------------------------------- #
def run(args):
    img = load_image(args.image, args.height)
    h, w, _ = img.shape

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 7, 60, 60)
    edges = cv2.Canny(blurred, 40, 130)

    labels, flat = segment(img, args.segments, args.seed)
    source = flat if args.flat else img
    parts = extract_parts(labels, args.segments, args.min_area)
    print(f"{len(parts)} parts found. ESC=quit  SPACE=pause  S=turbo")

    r = Renderer((w, h), args.speed, args.record)
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    r.show(canvas, wait=300)
    pos = [w // 2, h // 2]

    try:
        for part in parts:
            mask, (cx, cy) = part["mask"], part["center"]

            # A) trace the outline
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            for cnt in contours:
                if len(cnt) < 10:
                    continue
                # longer contours are sampled more coarsely so they don't drag
                step = max(args.step, len(cnt) // 250)
                pts = [tuple(p[0]) for p in cnt[::step]] + [tuple(cnt[0][0])]
                for prev, cur in zip(pts, pts[1:]):
                    cv2.line(canvas, prev, cur, INK, 2, cv2.LINE_AA)
                    if not r.show(canvas, cursor=cur):
                        return
                pos = list(pts[-1])

            # B) glide the cursor to the part's centre
            steps = 8
            for s in range(1, steps + 1):
                mx = int(pos[0] + (cx - pos[0]) * s / steps)
                my = int(pos[1] + (cy - pos[1]) * s / steps)
                if not r.show(canvas, cursor=(mx, my)):
                    return
            pos = [cx, cy]

            # C) fill colour with a top-to-bottom sweep
            top, height = part["bbox"]
            bands = max(1, args.fill_steps)
            for b in range(1, bands + 1):
                limit = top + int(height * b / bands)
                sub = mask.copy()
                sub[limit:, :] = 0
                canvas[sub > 0] = source[sub > 0]
                if not r.show(canvas, cursor=(cx, min(limit, h - 1)), wait=12):
                    return

        # Final crisp ink touch
        canvas[edges > 0] = (25, 25, 25)
        if r.writer:
            for _ in range(60):  # hold final frame ~2s in the video
                r.writer.write(canvas)
        cv2.imshow(WIN_NAME, canvas)
        if args.save:
            cv2.imwrite(args.save, canvas)
            print(f"Final image saved -> {args.save}")
        print("Sequential Art Complete! Press any key to exit.")
        cv2.waitKey(0)
    finally:
        r.close()


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description="Python Hanuman Art animator")
    p.add_argument("image", nargs="?", default=os.path.join(here, "animehanumanji.jpg"))
    p.add_argument("--segments", type=int, default=18, help="K-Means colour clusters")
    p.add_argument("--height", type=int, default=700, help="working image height (px)")
    p.add_argument("--min-area", type=int, default=120, help="ignore regions smaller than this")
    p.add_argument("--step", type=int, default=3, help="contour point skip (higher = faster)")
    p.add_argument("--fill-steps", type=int, default=6, help="bands in the fill sweep")
    p.add_argument("--speed", type=float, default=1.0, help="animation speed multiplier")
    p.add_argument("--flat", action="store_true", help="fill with flat cluster colours (cartoon look)")
    p.add_argument("--seed", type=int, default=42, help="K-Means seed for repeatable output")
    p.add_argument("--record", metavar="OUT.mp4", help="record the animation to a video")
    p.add_argument("--save", metavar="OUT.png", help="save the final image")
    return p.parse_args()


if __name__ == "__main__":
    try:
        run(parse_args())
    except FileNotFoundError as e:
        sys.exit(str(e))
