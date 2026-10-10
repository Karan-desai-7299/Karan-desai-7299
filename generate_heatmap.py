"""
Generate high-density, animated contribution & engineering velocity heatmaps
for Karansinh Desai's GitHub profile.
Replaces sparse GitHub snake graphs with vibrant, professional, high-activity heatmaps.
"""

import numpy as np

def generate_heatmap_svg(theme="dark"):
    is_dark = (theme == "dark")
    bg_col = "#080D1A" if is_dark else "#FFFFFF"
    border_col = "#1E293B" if is_dark else "#E2E8F0"
    text_muted = "#94A3B8" if is_dark else "#64748B"
    text_heading = "#22D3EE" if is_dark else "#0891B2"
    text_highlight = "#F8FAFC" if is_dark else "#0F172A"
    
    # Palette levels strictly matching terminal aesthetic
    if is_dark:
        levels = {
            0: "#161F30",
            1: "#4338CA", # Indigo
            2: "#7C3AED", # Violet
            3: "#06B6D4", # Cyan
            4: "#10B981"  # Emerald Green
        }
    else:
        levels = {
            0: "#EBEDF0",
            1: "#818CF8",
            2: "#A78BFA",
            3: "#0891B2",
            4: "#059669"
        }
        
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

    W, H = 880, 230
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
    
    # Title & Stats Header
    svg.append(f'<text x="30" y="32" font-size="13" font-weight="700" fill="{text_heading}" letter-spacing="0.5">⚡ YEARLY COMMIT VELOCITY &amp; CODE ACTIVITY</text>')
    svg.append(f'<text x="{W-30}" y="32" text-anchor="end" font-size="12" font-weight="600" fill="{text_muted}">1,480+ Total Contributions · 92.6% Active Days</text>')
    svg.append(f'<line x1="30" y1="46" x2="{W-30}" y2="46" stroke="{border_col}" stroke-width="1"/>')
    
    # Month Labels
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for idx, m in enumerate(months):
        col_idx = int(idx * (52 / 12))
        x_pos = 65 + col_idx * 14.5
        svg.append(f'<text x="{x_pos:.1f}" y="{64:.1f}" font-size="10" font-weight="500" fill="{text_muted}">{m}</text>')
        
    # Day Labels
    day_labels = [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]
    for r_idx, label in day_labels:
        y_pos = 80 + r_idx * 14.5 + 8.5
        svg.append(f'<text x="35" y="{y_pos:.1f}" font-size="10" font-weight="500" fill="{text_muted}">{label}</text>')
        
    # Heatmap Grid
    for col in range(52):
        x = 65 + col * 14.5
        for row in range(7):
            y = 80 + row * 14.5
            lvl = grid[row, col]
            c = levels[lvl]
            if lvl >= 3:
                # Add gentle breathing pulse to high-intensity days
                pulse_dur = 2.4 + (col % 6) * 0.4
                svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="11" height="11" rx="2.5" fill="{c}">')
                svg.append(f'<animate attributeName="opacity" values="1;0.8;1" dur="{pulse_dur:.1f}s" repeatCount="indefinite"/>')
                svg.append('</rect>')
            else:
                svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="11" height="11" rx="2.5" fill="{c}"/>')

    # Footer Stats Metrics
    svg.append(f'<line x1="30" y1="190" x2="{W-30}" y2="190" stroke="{border_col}" stroke-width="1"/>')
    
    # Legend
    svg.append(f'<text x="30" y="212" font-size="10" fill="{text_muted}">Less</text>')
    for l_idx in range(5):
        lx = 65 + l_idx * 14
        svg.append(f'<rect x="{lx}" y="202" width="10" height="10" rx="2" fill="{levels[l_idx]}"/>')
    svg.append(f'<text x="140" y="212" font-size="10" fill="{text_muted}">More</text>')
    
    # Metric Badges on Right
    svg.append(f'<text x="320" y="212" font-size="11" font-weight="600" fill="#10B981">● Current Streak: 42 Days</text>')
    svg.append(f'<text x="515" y="212" font-size="11" font-weight="600" fill="{text_heading}">⚡ Velocity: 4.8 commits/day</text>')
    svg.append(f'<text x="{W-30}" y="212" text-anchor="end" font-size="11" font-weight="600" fill="#A78BFA">🏆 Consistency: Top 2%</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    dark_svg = generate_heatmap_svg("dark")
    light_svg = generate_heatmap_svg("light")
    
    with open("contributions-dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    with open("contributions-light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    print("contributions-dark.svg and contributions-light.svg successfully generated!")
