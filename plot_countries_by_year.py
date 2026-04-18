import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import re
from matplotlib import rcParams
import matplotlib.cm as cm

# ─── Настройка шрифта ───────────────────────────────────────────────────────
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

def extract_year(y_str):
    if pd.isna(y_str):
        return None
    m = re.search(r'(\d{4})', str(y_str))
    return int(m.group(1)) if m else None

def extract_countries(c_str):
    if pd.isna(c_str):
        return []
    s = str(c_str)
    # Удаляем текст в скобках
    s = re.sub(r'\(.*?\)', '', s)
    # Разделяем по запятым и союзу "и"
    parts = re.split(r',| и ', s)
    res = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if 'АСЕАН' in p: p = 'АСЕАН'
        elif 'Многострановой' in p: p = 'Многострановой'
        res.append(p)
    return res

# ─── Чтение данных ────────────────────────────────────────────────────────────
df = pd.read_csv('Таблица_ЦШП.csv', encoding='utf-8')
df['Year'] = df['Год'].apply(extract_year)
df = df[(df['Year'] >= 2000) & (df['Year'] <= 2026)].copy()

records = []
for _, row in df.iterrows():
    countries = extract_countries(row['Страна'])
    y = row['Year']
    for c in countries:
        records.append({'Year': y, 'Country': c})

if not records:
    print("Не найдено данных для построения графика.")
    exit()

expanded_df = pd.DataFrame(records)

grouped = expanded_df.groupby(['Year', 'Country']).size().reset_index(name='Count')
pivot = grouped.pivot(index='Year', columns='Country', values='Count')

all_years = pd.DataFrame(index=range(2000, 2027))
pivot = all_years.join(pivot).fillna(0)

# Берём страны, у которых есть проекты, топ-10 лидеров
total_counts = pivot.sum().sort_values(ascending=False)
top_countries = total_counts.head(10).index.tolist()
pivot = pivot[top_countries]

COLORS = {
    "Малайзия": "#FF6B6B",
    "Сингапур": "#34D399",
    "Таиланд": "#4FC3F7",
    "Индонезия": "#F97316",
    "Вьетнам": "#A78BFA",
    "Филиппины": "#FFD93D",
    "АСЕАН": "#EC4899",
    "Камбоджа": "#60A5FA",
    "Лаос": "#86EFAC",
    "Многострановой": "#FBBF24",
    "Мьянма": "#E0E0E0",
    "Китай": "#FF0000"
}

cmap = cm.get_cmap('tab20', len(top_countries))
cdict = {}
for i, c in enumerate(top_countries):
    cdict[c] = COLORS.get(c, cmap(i))

def smooth(arr, w=2):
    kernel = np.ones(w) / w
    out = np.convolve(arr, kernel, mode='same')
    out[:w] = arr[:w]
    out[-w:] = arr[-w:]
    return out

# ─── Построение графика ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 9))
fig.patch.set_facecolor('#0F1117')
ax.set_facecolor('#171B28')

years = pivot.index.tolist()

for cat in top_countries:
    raw = pivot[cat].values
    color = cdict[cat]
    
    sm = smooth(raw, w=2)
    ax.fill_between(years, sm, alpha=0.08, color=color)
    ax.plot(years, sm, color=color, linewidth=1.2, alpha=0.35, linestyle='--')
    
    # Основная чёткая линия
    ax.plot(years, raw, color=color, linewidth=2.4,
            marker='o', markersize=6, markerfacecolor=color,
            markeredgecolor='#0F1117', markeredgewidth=1.5,
            label=cat, zorder=5)
            
    # Подписи пиков
    peak_idx = np.argmax(raw)
    if raw[peak_idx] > 1:
        ax.annotate(
            f" {int(raw[peak_idx])}",
            xy=(years[peak_idx], raw[peak_idx]),
            color=color, fontsize=8, fontweight='bold',
            va='bottom', ha='left',
            xytext=(4, 4), textcoords='offset points'
        )

# Вертикальные метки значимых событий
events = {
    2015: "Belt & Road",
    2019: "COVID /\nSafe City",
    2021: "5G-бум",
    2025: "AI-гонка",
}
for yr, label in events.items():
    ax.axvline(yr, color='#FFFFFF', linewidth=0.6, linestyle=':', alpha=0.3)
    # Позиция текста
    y_max = ax.get_ylim()[1]
    ax.text(yr + 0.15, y_max * 0.95 if y_max > 0 else 5,
            label, color='#AAAAAA', fontsize=7.5, va='top', rotation=0)

# Оформление осей
ax.set_xlim(1999.5, 2026.5)
ax.set_ylim(bottom=-0.1)
ax.set_xticks(range(2000, 2027))
ax.set_xticklabels([str(y) for y in range(2000, 2027)],
                   rotation=45, color='#BBBBBB', fontsize=9)
max_val = int(pivot.values.max())
ax.set_yticks(range(0, max_val + 2))
ax.set_yticklabels([str(i) for i in range(0, max_val + 2)],
                   color='#BBBBBB', fontsize=9)

ax.tick_params(axis='both', which='both', length=0)
ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

# Сетка
ax.yaxis.grid(True, color='#2A2F42', linewidth=0.8, zorder=0)
ax.xaxis.grid(True, color='#1E2236', linewidth=0.5, zorder=0)

# Заголовок
ax.set_title(
    'Динамика реализованных проектов по странам-лидерам\n(Цифровой Шёлковый путь в АСЕАН, 2000–2026)',
    color='#FFFFFF', fontsize=15, fontweight='bold', pad=18
)
ax.set_xlabel('Год', color='#888888', fontsize=11, labelpad=10)
ax.set_ylabel('Количество проектов', color='#888888', fontsize=11, labelpad=10)

# Легенда
legend = ax.legend(
    loc='upper left',
    frameon=True,
    facecolor='#1E2236',
    edgecolor='#2A2F42',
    labelcolor='#DDDDDD',
    fontsize=9,
    title='Топ стран',
    title_fontsize=9,
    ncol=1,
    handlelength=2.0,
    borderpad=0.8,
)
legend.get_title().set_color('#888888')

# Подпись автора
fig.text(0.99, 0.01, f'Источник: авторская база данных ЦШП, отображены лидеры',
         ha='right', va='bottom', color='#555577', fontsize=7.5, style='italic')

plt.tight_layout()
output = 'country_trends_chart.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"График по странам сохранён: {output}")
