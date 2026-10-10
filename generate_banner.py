"""
Master Banner Generator for Karansinh Desai's GitHub Profile
Produces animated terminal banners (dark.svg and light.svg) adhering strictly
to the Master Prompt specifications:
- Canvas: 1180x610
- Portrait: 300x340 Floyd-Steinberg 1-bit serpentine dither
- 94 Drift bands with per-dot Gaussian noise (sigma ~4)
- 60 Interleaved random intro groups (~3.2s)
- 900 Traveller dots morphing between Python, Code glyph </>, and React logos
  via Optimal Transport (linear_sum_assignment)
- 14.2s Indefinite animation loop with uneven keyTimes
- Locked SYSTEM.INFO rows with textLength + lengthAdjust and computed dotted leaders
"""

import os
import math
import time
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from scipy import ndimage
from scipy.optimize import linear_sum_assignment

def build_banner():
    print("=== Step 1: Processing Portrait Image ===")
    photo_path = 'input/photo.jpg'
    if not os.path.exists(photo_path):
        raise FileNotFoundError(f"Missing {photo_path}")
    
    im_raw = Image.open(photo_path).convert('RGB')
    # Head and shoulders crop:
    # Original is (1024, 1536).
    # Center crop width 1020, aspect ratio 300:340 -> height 1156.
    # Top at 40 (leaves 40px above hair, captures down to chest/shoulders)
    crop = im_raw.crop((2, 40, 1022, 1196))
    crop_300 = crop.resize((300, 340), Image.Resampling.LANCZOS)
    
    arr_rgb = np.array(crop_300, dtype=float)
    h, w, _ = arr_rgb.shape # 340, 300
    
    # Background Segmentation Mask:
    # Studio backdrop is high brightness (>185) and near zero color saturation (diff < 12)
    diff = arr_rgb.max(axis=2) - arr_rgb.min(axis=2)
    val = arr_rgb.max(axis=2)
    is_bg = (val > 185) & (diff < 12)
    is_bg = ndimage.binary_opening(is_bg, structure=np.ones((5, 5)))
    lbl, num = ndimage.label(is_bg)
    border = np.zeros_like(is_bg)
    border[0, :] = True
    border[:, 0] = True
    border[:, -1] = True
    border_labels = np.unique(lbl[border])
    border_labels = border_labels[border_labels > 0]
    true_bg = np.isin(lbl, border_labels)
    true_bg = ndimage.binary_dilation(true_bg, structure=np.ones((3, 3)))
    subject_mask = ~true_bg
    subject_mask = ndimage.binary_fill_holes(subject_mask)
    
    print(f"Subject mask calculated: coverage = {subject_mask.mean():.3f}")
    
    # Image Enhancements per Master Prompt:
    # Contrast 1.3x only, with autocontrast(cutoff=1) + UnsharpMask(radius=3, percent=140)
    gray = ImageOps.grayscale(crop_300)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.3)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    arr_gray = np.array(gray, dtype=float)
    
    # Serpentine Floyd-Steinberg Dithering
    def run_floyd_steinberg(intensity_map, active_mask=None):
        out = np.zeros((h, w), dtype=np.uint8)
        arr = intensity_map.copy().astype(float)
        
        for y in range(h):
            is_even = (y % 2 == 0)
            xs = range(w) if is_even else range(w - 1, -1, -1)
            direction = 1 if is_even else -1
            
            for x in xs:
                if active_mask is not None and not active_mask[y, x]:
                    arr[y, x] = 0.0
                    out[y, x] = 0
                    continue
                
                old_val = arr[y, x]
                new_val = 255.0 if old_val >= 128.0 else 0.0
                out[y, x] = 1 if new_val == 255.0 else 0
                err = old_val - new_val
                
                if direction == 1:
                    if x + 1 < w: arr[y, x + 1] += err * (7.0 / 16.0)
                    if y + 1 < h:
                        if x - 1 >= 0: arr[y + 1, x - 1] += err * (3.0 / 16.0)
                        arr[y + 1, x] += err * (5.0 / 16.0)
                        if x + 1 < w: arr[y + 1, x + 1] += err * (1.0 / 16.0)
                else:
                    if x - 1 >= 0: arr[y, x - 1] += err * (7.0 / 16.0)
                    if y + 1 < h:
                        if x + 1 < w: arr[y + 1, x + 1] += err * (3.0 / 16.0)
                        arr[y + 1, x] += err * (5.0 / 16.0)
                        if x - 1 >= 0: arr[y + 1, x - 1] += err * (1.0 / 16.0)
                        
        return out

    # Dark Mode intensity map:
    # Lit subject inside mask, zero outside, hair rim highlight to frame head
    arr_dark_map = arr_gray.copy()
    shirt_zone = np.zeros_like(arr_dark_map, dtype=bool)
    shirt_zone[220:, :] = True
    arr_dark_map[shirt_zone] = ((arr_dark_map[shirt_zone] / 255.0) ** 1.35) * 255.0
    eroded_mask = ndimage.binary_erosion(subject_mask, structure=np.ones((3, 3)))
    rim = subject_mask & (~eroded_mask)
    arr_dark_map[rim & (arr_gray < 100)] = 175.0
    arr_dark_map[~subject_mask] = 0.0
    dither_dark = run_floyd_steinberg(arr_dark_map, active_mask=subject_mask)
    print(f"Dark mode dots: {np.sum(dither_dark)}")

    # Light Mode intensity map:
    # Dots draw dark features of photo
    arr_light_map = (255.0 - arr_gray)
    arr_light_map[~subject_mask] = 0.0
    dither_light = run_floyd_steinberg(arr_light_map, active_mask=subject_mask)
    print(f"Light mode dots: {np.sum(dither_light)}")
    
    # Save source-of-truth arrays
    np.save('input/dither_dark.npy', dither_dark)
    np.save('input/dither_light.npy', dither_light)
    
    # Geometry and Layout
    # Canvas: 1180 x 610
    # Portrait placement: Frame x=45, y=90, w=390, h=475
    # Grid offset: x0 = 55, y0 = 120, pitch = 1.25 -> w=375, h=425
    x0, y0 = 55.0, 120.0
    pitch = 1.25
    cx = x0 + 150.0 * pitch # 242.5
    cy = y0 + 170.0 * pitch # 332.5
    
    # Build Dot Runs for efficient SVG (<path> horizontal runs)
    def extract_dot_coords(dither_grid):
        ys, xs = np.where(dither_grid > 0)
        canvas_x = x0 + xs * pitch
        canvas_y = y0 + ys * pitch
        return canvas_x, canvas_y, xs, ys

    dark_cx, dark_cy, dark_gx, dark_gy = extract_dot_coords(dither_dark)
    light_cx, light_cy, light_gx, light_gy = extract_dot_coords(dither_light)
    
    print("=== Step 2: Grouping Portrait into 94 Drift Bands ===")
    # Add per-dot Gaussian noise (sigma ~4) before grouping to prevent grid trap
    np.random.seed(42)
    def group_into_drift_bands(pts_x, pts_y, num_bands=94):
        n_dots = len(pts_x)
        noise_x = np.random.normal(0, 4.0, n_dots)
        noise_y = np.random.normal(0, 4.0, n_dots)
        
        # Radial + angular coordinate from center
        dx = (pts_x + noise_x) - cx
        dy = (pts_y + noise_y) - cy
        r = np.sqrt(dx**2 + dy**2)
        theta = np.arctan2(dy, dx)
        # Combined sorting metric for organic amoeba-like dissolution
        sort_metric = r + 25.0 * np.sin(3 * theta)
        
        # Quantile binning into num_bands
        quantiles = np.linspace(0, 100, num_bands + 1)
        bin_edges = np.percentile(sort_metric, quantiles)
        band_ids = np.digitize(sort_metric, bin_edges[1:-1])
        
        # Compute drift translation vectors:
        # Each band translates ~42% toward first logo centroid (cx, cy) while fading
        band_translations = []
        for b in range(num_bands):
            mask_b = (band_ids == b)
            if np.sum(mask_b) == 0:
                band_translations.append((0.0, 0.0))
                continue
            mean_bx = np.mean(pts_x[mask_b])
            mean_by = np.mean(pts_y[mask_b])
            # Vector toward logo centroid
            tx = 0.42 * (cx - mean_bx) + np.random.uniform(-4, 4)
            ty = 0.42 * (cy - mean_by) + np.random.uniform(-4, 4)
            band_translations.append((tx, ty))
            
        return band_ids, band_translations

    dark_band_ids, dark_translations = group_into_drift_bands(dark_cx, dark_cy, 94)
    light_band_ids, light_translations = group_into_drift_bands(light_cx, light_cy, 94)
    
    # Verify straight-boundary metric (contour irregularity)
    def measure_boundary_metric(band_ids, gx, gy):
        # Build 2D label map
        label_map = np.full((h, w), -1, dtype=int)
        for i in range(len(band_ids)):
            label_map[gy[i], gx[i]] = band_ids[i]
        # Check boundary variance across neighbors
        diff_h = np.abs(np.diff(label_map, axis=1))
        diff_v = np.abs(np.diff(label_map, axis=0))
        irregularity = (np.mean(diff_h > 0) + np.mean(diff_v > 0)) / 2.0
        return irregularity

    metric_dark = measure_boundary_metric(dark_band_ids, dark_gx, dark_gy)
    print(f"Organic boundary metric: {metric_dark:.4f} (organic ~ 0.01 - 0.05, grid ~ 0.17)")

    print("=== Step 3: Generating 60 Interleaved Random Intro Groups ===")
    # Uniform scatter across portrait for holographic shimmer intro
    def create_intro_groups(pts_x, pts_y, num_groups=60):
        n_dots = len(pts_x)
        # Random permutation gives uniform spatial coverage for each group
        perm = np.random.permutation(n_dots)
        group_ids = perm % num_groups
        return group_ids

    dark_intro_ids = create_intro_groups(dark_cx, dark_cy, 60)
    light_intro_ids = create_intro_groups(light_cx, light_cy, 60)

    print("=== Step 4: Generating 900 Traveller Dots & Optimal Transport ===")
    N_TRAVELLERS = 900
    
    # 1. Python Logo Points
    def sample_python_logo(N=900):
        py_img = Image.open('input/python.png').convert('L')
        arr = np.array(py_img)
        mask = arr < 240
        edges = mask ^ ndimage.binary_erosion(mask, structure=np.ones((3, 3)))
        ys, xs = np.where(edges)
        idx = np.round(np.linspace(0, len(xs) - 1, N)).astype(int)
        px = (xs[idx] - 112.5) / 112.5 * 85.0 + cx
        py = (ys[idx] - 112.5) / 112.5 * 85.0 + cy
        return np.column_stack([px, py])

    # 2. Code Glyph </> Points
    def sample_code_glyph(N=900):
        n_slash = 340
        n_bracket = (N - n_slash) // 2
        n_slash += N - (n_slash + 2 * n_bracket)
        pts = []
        n_arm = n_bracket // 2
        # <
        for i in range(n_arm):
            t = i / float(n_arm)
            pts.append([(cx - 30) * (1 - t) + (cx - 75) * t, (cy - 65) * (1 - t) + cy * t])
        for i in range(n_bracket - n_arm):
            t = i / float(n_bracket - n_arm)
            pts.append([(cx - 75) * (1 - t) + (cx - 30) * t, cy * (1 - t) + (cy + 65) * t])
        # /
        for i in range(n_slash):
            t = i / float(n_slash)
            pts.append([(cx + 22) * (1 - t) + (cx - 22) * t, (cy - 75) * (1 - t) + (cy + 75) * t])
        # >
        for i in range(n_arm):
            t = i / float(n_arm)
            pts.append([(cx + 30) * (1 - t) + (cx + 75) * t, (cy - 65) * (1 - t) + cy * t])
        for i in range(n_bracket - n_arm):
            t = i / float(n_bracket - n_arm)
            pts.append([(cx + 75) * (1 - t) + (cx + 30) * t, cy * (1 - t) + (cy + 65) * t])
        return np.array(pts)

    # 3. React Logo Points
    def sample_react_logo(N=900):
        n_center = 120
        n_per_ellipse = (N - n_center) // 3
        n_center += N - (n_center + 3 * n_per_ellipse)
        pts = []
        for i in range(n_center):
            th = 2 * np.pi * i / n_center
            r = 16.0 * np.sqrt((i + 1) / n_center)
            pts.append([cx + r * np.cos(th), cy + r * np.sin(th)])
        a, b = 78.0, 28.0
        for rot_deg in [0, 60, 120]:
            rot = np.radians(rot_deg)
            R = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]])
            for i in range(n_per_ellipse):
                th = 2 * np.pi * i / n_per_ellipse
                p = R @ np.array([a * np.cos(th), b * np.sin(th)])
                pts.append([cx + p[0], cy + p[1]])
        return np.array(pts)

    pts_logo1 = sample_python_logo(N_TRAVELLERS)
    pts_logo2 = sample_code_glyph(N_TRAVELLERS)
    pts_logo3 = sample_react_logo(N_TRAVELLERS)

    # Optimal Transport Matching:
    # Match logo1 -> logo2
    cost_12 = np.sum((pts_logo1[:, None, :] - pts_logo2[None, :, :]) ** 2, axis=2)
    _, perm_2 = linear_sum_assignment(cost_12)
    pts_logo2_opt = pts_logo2[perm_2]

    # Match logo2 -> logo3
    cost_23 = np.sum((pts_logo2_opt[:, None, :] - pts_logo3[None, :, :]) ** 2, axis=2)
    _, perm_3 = linear_sum_assignment(cost_23)
    pts_logo3_opt = pts_logo3[perm_3]

    print("Optimal transport matching completed for 900 dots across 3 logos.")

    # Convert a 2D binary grid slice into compact horizontal <path> runs
    def grid_slice_to_path_d(binary_grid):
        cmds = []
        for y in range(h):
            row = binary_grid[y]
            if not np.any(row):
                continue
            canvas_y = y0 + y * pitch
            in_run = False
            start_x = 0
            for x in range(w):
                if row[x] and not in_run:
                    in_run = True
                    start_x = x
                elif not row[x] and in_run:
                    in_run = False
                    cx_pos = x0 + start_x * pitch
                    run_len = (x - start_x) * pitch
                    cmds.append(f"M{cx_pos:.1f},{canvas_y:.1f}h{run_len:.2f}")
            if in_run:
                cx_pos = x0 + start_x * pitch
                run_len = (w - start_x) * pitch
                cmds.append(f"M{cx_pos:.1f},{canvas_y:.1f}h{run_len:.2f}")
        return "".join(cmds)

    print("=== Step 5: Building SVG Documents ===")
    
    # Info Panel Rows Specification for Karansinh Desai:
    info_rows = [
        # Section 1: Identity & Core Details
        ("Subject", "Karansinh Desai"),
        ("Role", "Full-Stack Dev · AI/ML"),
        ("Origin", "Kolhapur, India"),
        ("Education", "B.Tech CSE (2023-27)"),
        ("Status", "Building + Learning + Shipping"),
        ("ToolChain", "VS Code · Git · Postman · Vercel"),
        # Section 2: Technical Skills
        ("Core.Lang", "Python · JavaScript · SQL"),
        ("Core.Frontend", "React.js · Tailwind · Vite"),
        ("Core.Backend", "Node.js · FastAPI · Express"),
        ("Core.Database", "MongoDB · Supabase · MySQL"),
        ("Core.Infra", "PyTorch · Scikit-learn · Groq"),
        # Section 3: Professional Links
        ("Grid.Mail", "karansinhdesai91@gmail.com"),
        ("Grid.Portfolio", "karansinh-portfolio.vercel.app"),
        ("Grid.LinkedIn", "in/karansinh-desai"),
        ("Grid.GitHub", "github.com/Karan-desai-7299"),
        ("Grid.LeetCode", "leetcode.com/u/karan_desai_")
    ]

    def render_svg(theme="dark"):
        is_dark = (theme == "dark")
        # Palettes strictly per specification:
        # Portrait: [#A78BFA dark / #7C3AED light]
        # UI chrome: [#22D3EE / #0891B2]
        # accent: [#10B981]
        # background: [#0A101F]
        bg_col = "#0A101F" if is_dark else "#F8FAFC"
        card_bg = "#080D1A" if is_dark else "#FFFFFF"
        border_col = "#1E293B" if is_dark else "#E2E8F0"
        title_col = "#94A3B8" if is_dark else "#64748B"
        chrome_col = "#22D3EE" if is_dark else "#0891B2"
        portrait_col = "#A78BFA" if is_dark else "#7C3AED"
        accent_col = "#10B981" if is_dark else "#059669"
        text_val_col = "#F8FAFC" if is_dark else "#0F172A"
        dot_leader_col = "#334155" if is_dark else "#CBD5E1"
        
        cur_cx = dark_cx if is_dark else light_cx
        cur_cy = dark_cy if is_dark else light_cy
        cur_gx = dark_gx if is_dark else light_gx
        cur_gy = dark_gy if is_dark else light_gy
        cur_band_ids = dark_band_ids if is_dark else light_band_ids
        cur_translations = dark_translations if is_dark else light_translations
        cur_intro_ids = dark_intro_ids if is_dark else light_intro_ids

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 610" width="1180" height="610" style="background:{bg_col};">')
        svg.append('<defs>')
        svg.append('<style>')
        svg.append('@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap");')
        svg.append('text { font-family: "JetBrains Mono", "Fira Code", monospace; }')
        svg.append('</style>')
        svg.append('</defs>')

        # Window Frame
        svg.append(f'<rect x="15" y="15" width="1150" height="580" rx="14" fill="{bg_col}" stroke="{border_col}" stroke-width="1.5"/>')
        
        # Terminal Header Bar
        svg.append(f'<circle cx="45" cy="45" r="6" fill="#EF4444"/>')
        svg.append(f'<circle cx="65" cy="45" r="6" fill="#F59E0B"/>')
        svg.append(f'<circle cx="85" cy="45" r="6" fill="#10B981"/>')
        svg.append(f'<text x="590" y="49" text-anchor="middle" font-size="13" font-weight="600" fill="{title_col}">profile.sh --live</text>')
        svg.append(f'<line x1="15" y1="70" x2="1165" y2="70" stroke="{border_col}" stroke-width="1"/>')

        # Left Portrait Frame (~38%)
        svg.append(f'<rect x="45" y="90" width="390" height="475" rx="8" fill="{card_bg}" stroke="{border_col}" stroke-width="1"/>')
        svg.append(f'<text x="60" y="112" font-size="12" font-weight="700" fill="{chrome_col}" letter-spacing="1">VISUAL.MAP</text>')
        svg.append(f'<text x="365" y="112" font-size="10" fill="{title_col}">300x340</text>')

        # Right Info Panel Frame (~62%)
        svg.append(f'<rect x="455" y="90" width="680" height="475" rx="8" fill="{card_bg}" stroke="{border_col}" stroke-width="1"/>')
        svg.append(f'<text x="475" y="115" font-size="13" font-weight="700" fill="{chrome_col}" letter-spacing="1">SYSTEM.INFO</text>')

        # Pulsing Red LIVE Badge
        svg.append(f'<circle cx="955" cy="111" r="4.5" fill="#EF4444">')
        svg.append('<animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite"/>')
        svg.append('</circle>')
        svg.append(f'<text x="966" y="115" font-size="11" font-weight="700" fill="#EF4444" letter-spacing="0.5">LIVE</text>')

        # Pill Badge with Handle
        pill_fill = "#1E293B" if is_dark else "#F1F5F9"
        svg.append(f'<rect x="1010" y="100" width="110" height="22" rx="11" fill="{pill_fill}" stroke="{chrome_col}" stroke-width="1"/>')
        svg.append(f'<text x="1065" y="115" text-anchor="middle" font-size="11" font-weight="600" fill="{chrome_col}">@karan-desai</text>')

        # SYSTEM.INFO Rows with Locked textLength & Computed Dotted Leaders
        y_start = 145
        row_h = 24.5
        for idx, (label, val_str) in enumerate(info_rows):
            cur_y = y_start + idx * row_h
            # Dotted leaders computed from label/value lengths
            w_label = len(label) * 8.4 + 4
            w_val = len(val_str) * 8.0 + 4
            
            x_label = 475
            x_val_right = 1115
            x_val = x_val_right - w_val
            
            x_lead_start = x_label + w_label + 10
            x_lead_end = x_val - 10
            
            # Row Label (Locked with textLength + lengthAdjust)
            svg.append(f'<text x="{x_label}" y="{cur_y}" font-size="13" font-weight="600" fill="{chrome_col}" textLength="{w_label:.1f}" lengthAdjust="spacingAndGlyphs">{label}</text>')
            # Computed Dotted Leader
            if x_lead_end > x_lead_start:
                svg.append(f'<line x1="{x_lead_start:.1f}" y1="{cur_y - 4}" x2="{x_lead_end:.1f}" y2="{cur_y - 4}" stroke="{dot_leader_col}" stroke-dasharray="2,5" stroke-width="1.5"/>')
            # Row Value (Locked with textLength + lengthAdjust)
            svg.append(f'<text x="{x_val:.1f}" y="{cur_y}" font-size="13" font-weight="500" fill="{text_val_col}" textLength="{w_val:.1f}" lengthAdjust="spacingAndGlyphs">{val_str}</text>')

        # PORTRAIT INTRO LAYER (~3.2s once, 60 interleaved random groups)
        # Fades in over 2s, vanishes at 3.2s when the loop takes over
        svg.append('<!-- Portrait Intro Layer: 60 Interleaved Shimmer Groups -->')
        svg.append('<g id="intro-layer">')
        svg.append('<animate attributeName="opacity" dur="3.2s" fill="freeze" values="1;1;0" keyTimes="0;0.9;1"/>')
        for g_idx in range(60):
            mask_g = (cur_intro_ids == g_idx)
            if np.sum(mask_g) == 0:
                continue
            sub_grid = np.zeros((h, w), dtype=bool)
            sub_grid[cur_gy[mask_g], cur_gx[mask_g]] = True
            path_d = grid_slice_to_path_d(sub_grid)
            delay = (g_idx / 60.0) * 1.8
            svg.append(f'<g opacity="0">')
            svg.append(f'<animate attributeName="opacity" dur="0.4s" begin="{delay:.2f}s" fill="freeze" values="0;1"/>')
            svg.append(f'<path d="{path_d}" stroke="{portrait_col}" stroke-width="1.25" shape-rendering="crispEdges"/>')
            svg.append('</g>')
        svg.append('</g>')

        # PORTRAIT LOOP LAYER (~14.2s, 94 drift bands)
        svg.append('<!-- Portrait Loop Layer: 94 Drift Bands -->')
        svg.append('<g id="portrait-loop" opacity="0">')
        svg.append('<animate attributeName="opacity" dur="14.2s" repeatCount="indefinite" values="1;1;0;0;0;0;0;0;1" keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"/>')
        
        for b_idx in range(94):
            mask_b = (cur_band_ids == b_idx)
            if np.sum(mask_b) == 0:
                continue
            sub_grid = np.zeros((h, w), dtype=bool)
            sub_grid[cur_gy[mask_b], cur_gx[mask_b]] = True
            path_d = grid_slice_to_path_d(sub_grid)
            tx, ty = cur_translations[b_idx]
            svg.append('<g>')
            svg.append(f'<animateTransform attributeName="transform" type="translate" dur="14.2s" repeatCount="indefinite" values="0,0; 0,0; {tx:.1f},{ty:.1f}; {tx:.1f},{ty:.1f}; {tx:.1f},{ty:.1f}; {tx:.1f},{ty:.1f}; {tx:.1f},{ty:.1f}; {tx:.1f},{ty:.1f}; 0,0" keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"/>')
            svg.append(f'<path d="{path_d}" stroke="{portrait_col}" stroke-width="1.25" shape-rendering="crispEdges"/>')
            svg.append('</g>')
        svg.append('</g>')

        # TRAVELLERS LAYER (~900 dots morphing across Python, Code </>, React logos)
        # Opacity: hidden during portrait hold (0 to 3.0s), fades in during drift (3.0 to 4.3s),
        # holds solid for Logo 1 (4.3 to 6.3s), morphs to Logo 2 (6.3 to 7.6s), holds Logo 2 (7.6 to 9.6s),
        # morphs to Logo 3 (9.6 to 10.9s), holds Logo 3 (10.9 to 12.9s), dissolves back (12.9 to 14.2s).
        svg.append('<!-- Travellers Layer: 900 Optimal Transport Morphing Dots -->')
        traveller_col = chrome_col # High-tech glowing cyan UI chrome color for logos
        svg.append('<g id="travellers" opacity="0">')
        svg.append('<animate attributeName="opacity" dur="14.2s" repeatCount="indefinite" values="0;0;1;1;1;1;1;0;0" keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"/>')
        
        for i in range(N_TRAVELLERS):
            p1 = pts_logo1[i]
            p2 = pts_logo2_opt[i]
            p3 = pts_logo3_opt[i]
            
            # Values:
            # t0 (0s): p1
            # t1 (3.0s): p1
            # t2 (4.3s): p1 (assemble Logo 1)
            # t3 (6.3s): p1 (hold Logo 1)
            # t4 (7.6s): p2 (morph to Logo 2)
            # t5 (9.6s): p2 (hold Logo 2)
            # t6 (10.9s): p3 (morph to Logo 3)
            # t7 (12.9s): p3 (hold Logo 3)
            # t8 (14.2s): p1 (return)
            vx = f"{p1[0]:.1f}; {p1[0]:.1f}; {p1[0]:.1f}; {p1[0]:.1f}; {p2[0]:.1f}; {p2[0]:.1f}; {p3[0]:.1f}; {p3[0]:.1f}; {p1[0]:.1f}"
            vy = f"{p1[1]:.1f}; {p1[1]:.1f}; {p1[1]:.1f}; {p1[1]:.1f}; {p2[1]:.1f}; {p2[1]:.1f}; {p3[1]:.1f}; {p3[1]:.1f}; {p1[1]:.1f}"
            
            svg.append(f'<circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="1.6" fill="{traveller_col}">')
            svg.append(f'<animate attributeName="cx" dur="14.2s" repeatCount="indefinite" values="{vx}" keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"/>')
            svg.append(f'<animate attributeName="cy" dur="14.2s" repeatCount="indefinite" values="{vy}" keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"/>')
            svg.append('</circle>')
        svg.append('</g>')

        svg.append('</svg>')
        return "\n".join(svg)

    dark_svg = render_svg("dark")
    light_svg = render_svg("light")

    with open("dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    with open("light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)

    print(f"dark.svg generated successfully! File size: {len(dark_svg) / 1024:.1f} KB")
    print(f"light.svg generated successfully! File size: {len(light_svg) / 1024:.1f} KB")

if __name__ == "__main__":
    t0 = time.time()
    build_banner()
    print(f"Complete pipeline finished in {time.time() - t0:.2f}s")
