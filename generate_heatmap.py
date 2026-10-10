"""
Generate high-density, animated contribution snake SVGs
(contributions-dark.svg and contributions-light.svg)
Features a vibrant 52-week activity grid with a sleek 5-segment snake slithering across it.
"""

import numpy as np

def build_snake_heatmap(theme="dark"):
    is_dark = (theme == "dark")
    bg_col = "#080D1A" if is_dark else "#FFFFFF"
    border_col = "#1E293B" if is_dark else "#E2E8F0"
    text_muted = "#94A3B8" if is_dark else "#64748B"
    text_heading = "#22D3EE" if is_dark else "#0891B2"
    
    # Palette levels matching Image 2
    if is_dark:
        levels = {
            0: "#161F30",
            1: "#4338CA", # Indigo
            2: "#7C3AED", # Violet
            3: "#06B6D4", # Cyan
            4: "#10B981"  # Emerald Green
        }
        snake_colors = ["#10B981", "#22D3EE", "#06B6D4", "#8B5CF6", "#A78BFA"]
    else:
        levels = {
            0: "#EBEDF0",
            1: "#818CF8",
            2: "#A78BFA",
            3: "#0891B2",
            4: "#059669"
        }
        snake_colors = ["#059669", "#0891B2", "#06B6D4", "#7C3AED", "#6366F1"]

    # 52 weeks x 7 days grid with high activity
    np.random.seed(101)
    grid = np.zeros((7, 52), dtype=int)
    for col in range(52):
        for row in range(7):
            is_weekday = (row in [1, 2, 3, 4, 5])
            prob = 0.93 if is_weekday else 0.75
            if np.random.rand() < prob:
                weights = [0.12, 0.28, 0.38, 0.22] if is_weekday else [0.35, 0.40, 0.20, 0.05]
                grid[row, col] = np.random.choice([1, 2, 3, 4], p=weights)
            else:
                grid[row, col] = 0

    # Hamiltonian cyclic path covering all rows
    path = []
    for c in range(0, 51): path.append((c, 0))
    path.append((50, 1))
    for c in range(49, 0, -1): path.append((c, 1))
    path.append((1, 2))
    for c in range(2, 51): path.append((c, 2))
    path.append((50, 3))
    for c in range(49, 0, -1): path.append((c, 3))
    path.append((1, 4))
    for c in range(2, 51): path.append((c, 4))
    path.append((50, 5))
    for c in range(49, 0, -1): path.append((c, 5))
    path.append((1, 6))
    for c in range(2, 52): path.append((c, 6))
    for r in range(5, -1, -1): path.append((51, r))
    for c in range(50, -1, -1): path.append((c, 0))

    clean_path = []
    for p in path:
        if not clean_path or clean_path[-1] != p:
            clean_path.append(p)
    if clean_path[-1] == clean_path[0]:
        clean_path = clean_path[:-1]

    N_STEPS = len(clean_path)
    DUR = 28.0 # 28 seconds total loop
    
    W, H = 880, 230
    x0, y0 = 65.0, 80.0
    pitch = 14.5
    
    # Precompute canvas coordinates for each step
    canvas_pts = [(x0 + c * pitch, y0 + r * pitch) for (c, r) in clean_path]
    
    # keyTimes string
    kt_vals = [f"{i / N_STEPS:.4f}" for i in range(N_STEPS)] + ["1.0000"]
    kt_str = ";".join(kt_vals)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" style="background:{bg_col}; border-radius:12px;">')
    svg.append('<defs>')
    svg.append('<style>')
    svg.append('@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap");')
    svg.append('text { font-family: "JetBrains Mono", monospace; }')
    svg.append('</style>')
    svg.append('</defs>')
    
    # Card Border
    svg.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="{bg_col}" stroke="{border_col}" stroke-width="1.5"/>')
    
    # Header
    svg.append(f'<text x="30" y="32" font-size="13" font-weight="700" fill="{text_heading}" letter-spacing="0.5">⚡ YEARLY COMMIT VELOCITY &amp; CODE ACTIVITY</text>')
    svg.append(f'<text x="{W-30}" y="32" text-anchor="end" font-size="12" font-weight="600" fill="{text_muted}">1,480+ Total Contributions · 92.6% Active Days</text>')
    svg.append(f'<line x1="30" y1="46" x2="{W-30}" y2="46" stroke="{border_col}" stroke-width="1"/>')
    
    # Month Labels
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for idx, m in enumerate(months):
        col_idx = int(idx * (52 / 12))
        x_pos = x0 + col_idx * pitch
        svg.append(f'<text x="{x_pos:.1f}" y="64" font-size="10" font-weight="500" fill="{text_muted}">{m}</text>')
        
    # Day Labels
    day_labels = [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]
    for r_idx, label in day_labels:
        y_pos = y0 + r_idx * pitch + 8.5
        svg.append(f'<text x="35" y="{y_pos:.1f}" font-size="10" font-weight="500" fill="{text_muted}">{label}</text>')
        
    # Base Contribution Grid
    for col in range(52):
        x = x0 + col * pitch
        for row in range(7):
            y = y0 + row * pitch
            lvl = grid[row, col]
            c = levels[lvl]
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="11" height="11" rx="2.5" fill="{c}"/>')

    # ANIMATED SNAKE BODY (5 Segments)
    SNAKE_LEN = 5
    for s_idx in range(SNAKE_LEN):
        color = snake_colors[s_idx]
        # Delayed position for each body segment
        seg_pts = []
        for step in range(N_STEPS):
            delayed_step = (step - s_idx) % N_STEPS
            seg_pts.append(canvas_pts[delayed_step])
        seg_pts.append(seg_pts[0]) # close loop
        
        # Translate values
        trans_vals = ";".join([f"{px:.1f},{py:.1f}" for px, py in seg_pts])
        
        # Segment sizing: head is slightly larger with rounded corners
        size = 12.0 if s_idx == 0 else 10.5
        rx = 3.5 if s_idx == 0 else 2.5
        offset = (11.0 - size) / 2.0
        
        svg.append(f'<!-- Snake Segment {s_idx} -->')
        svg.append(f'<g>')
        svg.append(f'<rect x="{offset:.1f}" y="{offset:.1f}" width="{size:.1f}" height="{size:.1f}" rx="{rx:.1f}" fill="{color}" stroke="{bg_col}" stroke-width="0.8">')
        if s_idx == 0:
            # Subtle glow filter or pulse on head
            svg.append(f'<animate attributeName="opacity" values="1;0.85;1" dur="1.2s" repeatCount="indefinite"/>')
        svg.append('</rect>')
        svg.append(f'<animateTransform attributeName="transform" type="translate" dur="{DUR}s" repeatCount="indefinite" values="{trans_vals}" keyTimes="{kt_str}"/>')
        svg.append('</g>')

    # Footer
    svg.append(f'<line x1="30" y1="190" x2="{W-30}" y2="190" stroke="{border_col}" stroke-width="1"/>')
    svg.append(f'<text x="30" y="212" font-size="10" fill="{text_muted}">Less</text>')
    for l_idx in range(5):
        lx = 65 + l_idx * 14
        svg.append(f'<rect x="{lx}" y="202" width="10" height="10" rx="2" fill="{levels[l_idx]}"/>')
    svg.append(f'<text x="140" y="212" font-size="10" fill="{text_muted}">More</text>')
    
    svg.append(f'<text x="320" y="212" font-size="11" font-weight="600" fill="#10B981">● Current Streak: 42 Days</text>')
    svg.append(f'<text x="515" y="212" font-size="11" font-weight="600" fill="{text_heading}">⚡ Velocity: 4.8 commits/day</text>')
    svg.append(f'<text x="{W-30}" y="212" text-anchor="end" font-size="11" font-weight="600" fill="#A78BFA">🏆 Consistency: Top 2%</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    dark_svg = build_snake_heatmap("dark")
    light_svg = build_snake_heatmap("light")
    with open("contributions-dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    with open("contributions-light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
    print("Snake heatmaps updated successfully!")
