import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import re
import numpy as np
from matplotlib import rcParams

# ─── Настройка шрифта ───────────────────────────────────────────────────────
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

# ─── Категории технологий ─────────────────────────────────────────────────────
TECH_MAP = {
    "5G":                     ["5g"],
    "Телекоммуникации / 4G":  ["4g", "мобильная", "телекоммуникац"],
    # Подводные кабели: добавлены "инфраструктур" — охватывает N17, 21, 22, 36, 43, 48
    "Подводные кабели":       ["кабель", "подводн", "инфраструктур"],
    "Облачные технологии":    ["облач", "дата-центр", "cloud", "цод", "вычислен"],
    "Умный город":            ["умный город", "safe city", "безопасный город"],
    "ИИ / Умный завод":       ["ии / ", "искусственный", " ии", "ai", "умный завод"],
    # E-Commerce: добавлены "финансов" (e-CNY N40) и "электронное управление" (N4 → ЖД ниже)
    "E-Commerce / Финтех":    ["коммерц", "финтех", "платёж", "платеж", "финансов"],
    "Спутниковые технологии": ["спутник", "навигац", "beidou"],
    # ЖД: добавлено "электронное управление" — охватывает N4 (поезда на Китайско-Лаосской ж/д)
    "ЖД-инфраструктура":      ["железнодорож", "электронное управление"],
    "Дроны / АгроТех":     ["агро", "дрон", "сельское"],
}

COLORS = {
    "5G":                     "#FF6B6B",
    "Телекоммуникации / 4G":  "#FFD93D",
    "Подводные кабели":       "#4FC3F7",
    "Облачные технологии":    "#A78BFA",
    "Умный город":            "#34D399",
    "ИИ / Умный завод":       "#F97316",
    "E-Commerce / Финтех":    "#EC4899",
    "Спутниковые технологии": "#60A5FA",
    "ЖД-инфраструктура":      "#FBBF24",
    "Дроны / АгроТех":        "#86EFAC",
}

def classify(tech_str):
    if pd.isna(tech_str):
        return "Прочее"
    s = tech_str.lower()
    for category, keywords in TECH_MAP.items():
        for kw in keywords:
            if kw in s:
                return category
    return "Прочее"

def extract_year(y_str):
    if pd.isna(y_str):
        return None
    m = re.search(r'(\d{4})', str(y_str))
    return int(m.group(1)) if m else None

# ─── Чтение данных ────────────────────────────────────────────────────────────
df = pd.read_csv('Таблица_ЦШП.csv', encoding='utf-8')
df['Year']      = df['Год'].apply(extract_year)
df['Tech_Cat']  = df['Тип технологии'].apply(classify)
df = df[(df['Year'] >= 2000) & (df['Year'] <= 2025)].copy()

grouped = df.groupby(['Year', 'Tech_Cat']).size().reset_index(name='Count')
pivot   = grouped.pivot(index='Year', columns='Tech_Cat', values='Count')
all_years = pd.DataFrame(index=range(2000, 2026))
pivot = all_years.join(pivot).fillna(0)

# Только те категории, у которых есть хоть один проект
cats = [c for c in COLORS.keys() if c in pivot.columns and pivot[c].sum() > 0]
pivot = pivot[cats]

# ─── Сглаживание (скользящее среднее 1 год – сохраняем точность, НО
#     дополнительно рисуем сглаженную фоновую линию) ─────────────────────────
def smooth(arr, w=2):
    kernel = np.ones(w) / w
    out = np.convolve(arr, kernel, mode='same')
    # Края оставляем как есть (не сглаживаем)
    out[:w] = arr[:w]
    out[-w:] = arr[-w:]
    return out

# ─── Построение графика ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 9))

# Тёмный фон
fig.patch.set_facecolor('#0F1117')
ax.set_facecolor('#171B28')

years = pivot.index.tolist()

for cat in cats:
    raw    = pivot[cat].values
    color  = COLORS[cat]

    # Фоновая плавная линия (сглаженная)
    sm = smooth(raw, w=2)
    ax.fill_between(years, sm, alpha=0.08, color=color)
    ax.plot(years, sm, color=color, linewidth=1.2, alpha=0.35, linestyle='--')

    # Основная чёткая линия по реальным данным
    ax.plot(years, raw, color=color, linewidth=2.4,
            marker='o', markersize=6, markerfacecolor=color,
            markeredgecolor='#0F1117', markeredgewidth=1.5,
            label=cat, zorder=5)

    # Подписи только для максимальных значений > 1
    peak_idx = np.argmax(raw)
    if raw[peak_idx] > 1:
        ax.annotate(
            f" {int(raw[peak_idx])}",
            xy=(years[peak_idx], raw[peak_idx]),
            color=color, fontsize=8, fontweight='bold',
            va='bottom', ha='left',
            xytext=(4, 4), textcoords='offset points'
        )

# ─── Вертикальные метки значимых событий ─────────────────────────────────────
events = {
    2015: "Belt & Road",
    2019: "COVID /\nSafe City",
    2021: "5G-бум",
    2025: "AI-гонка",
}
for yr, label in events.items():
    ax.axvline(yr, color='#FFFFFF', linewidth=0.6, linestyle=':', alpha=0.3)
    ax.text(yr + 0.15, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 5,
            label, color='#AAAAAA', fontsize=7.5, va='top', rotation=0)

# ─── Оформление осей ──────────────────────────────────────────────────────────
ax.set_xlim(1999.5, 2025.5)
ax.set_ylim(bottom=-0.1)
ax.set_xticks(range(2000, 2026))
ax.set_xticklabels([str(y) for y in range(2000, 2026)],
                   rotation=45, color='#BBBBBB', fontsize=9)
ax.set_yticks(range(0, int(pivot.values.max()) + 2))
ax.set_yticklabels([str(i) for i in range(0, int(pivot.values.max()) + 2)],
                   color='#BBBBBB', fontsize=9)

ax.tick_params(axis='both', which='both', length=0)
ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

# Сетка
ax.yaxis.grid(True, color='#2A2F42', linewidth=0.8, zorder=0)
ax.xaxis.grid(True, color='#1E2236', linewidth=0.5, zorder=0)

# ─── Заголовок и подписи ──────────────────────────────────────────────────────
ax.set_title(
    'Динамика реализованных проектов по типу технологии\n(Цифровой Шёлковый путь в АСЕАН, 2000–2025)',
    color='#FFFFFF', fontsize=15, fontweight='bold', pad=18
)
ax.set_xlabel('Год', color='#888888', fontsize=11, labelpad=10)
ax.set_ylabel('Количество проектов', color='#888888', fontsize=11, labelpad=10)

# ─── Легенда ──────────────────────────────────────────────────────────────────
legend = ax.legend(
    loc='upper left',
    frameon=True,
    facecolor='#1E2236',
    edgecolor='#2A2F42',
    labelcolor='#DDDDDD',
    fontsize=9,
    title='Тип технологии',
    title_fontsize=9,
    ncol=1,
    handlelength=2.0,
    borderpad=0.8,
)
legend.get_title().set_color('#888888')

# ─── Подпись источника ────────────────────────────────────────────────────────
fig.text(0.99, 0.01, 'Источник: авторская база данных ЦШП, 85 проектов',
         ha='right', va='bottom', color='#555577', fontsize=7.5, style='italic')

plt.tight_layout()
output = 'tech_trends_chart.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"График сохранён: {output}")
