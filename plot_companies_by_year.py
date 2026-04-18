import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from matplotlib import rcParams
import matplotlib.cm as cm

# --- Настройка шрифтов ---
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

def extract_year(y_str):
    if pd.isna(y_str):
        return None
    m = re.search(r'(\d{4})', str(y_str))
    return int(m.group(1)) if m else None

def clean_company(c_str):
    c = str(c_str).strip()
    
    # Группировка дочерних брендов в материнские холдинги
    # Huawei
    if re.search(r'Huawei|HMN Tech|Huawei Marine|HMN Technology', c, re.I):
        return "Huawei"
    # Alibaba
    if re.search(r'Alibaba|Lazada|Ant Group|Alipay|Aliyun|Ant International', c, re.I):
        return "Alibaba"
    # Tencent
    if re.search(r'Tencent|WeChat|Weixin|Joox|WeTv', c, re.I):
        return "Tencent"
    # ByteDance
    if re.search(r'ByteDance|TikTok', c, re.I):
        return "ByteDance"
    # China Mobile
    if re.search(r'China Mobile|CMI', c, re.I):
        return "China Mobile"
    # ZTE
    if re.search(r'ZTE', c, re.I):
        return "ZTE"
    # China Telecom
    if re.search(r'China Telecom', c, re.I):
        return "China Telecom"
    # Baidu
    if re.search(r'Baidu|Xiaodu', c, re.I):
        return "Baidu"
    # Xiaomi
    if re.search(r'Xiaomi', c, re.I):
        return "Xiaomi"
    
    return c

def extract_companies(c_str):
    if pd.isna(c_str):
        return []
    s = str(c_str)
    # Разделяем по запятым и союзу "и"
    parts = re.split(r',| и ', s)
    res = []
    for p in parts:
        p = p.strip()
        # Игнорируем слишком короткие имена, пустые строки и записи без букв
        if not p or len(p) < 2 or not re.search(r'[a-zA-Zа-яА-Я]', p):
            continue
        
        # Список исключений для не-коммерческих сущностей
        low_p = p.lower()
        if any(x in low_p for x in ['асеан', 'bank', 'мид', 'кнр', 'правительство', 'министерство', 'центр']):
            continue
            
        cleaned = clean_company(p)
        res.append(cleaned)
    # Возвращаем уникальные компании для одной строки после очистки
    return list(set(res))

# --- Основная логика ---
try:
    df = pd.read_csv('Таблица_ЦШП.csv', encoding='utf-8')
except FileNotFoundError:
    print("Ошибка: Файл 'Таблица_ЦШП.csv' не найден.")
    exit()

df['Year'] = df['Год'].apply(extract_year)
df = df[(df['Year'] >= 2000) & (df['Year'] <= 2026)].copy()

records = []
for _, row in df.iterrows():
    comps = extract_companies(row['Компания или оператор'])
    y = row['Year']
    for comp in comps:
        records.append({'Year': y, 'Company': comp})

if not records:
    print("Данные компаний не найдены или не удалось распознать.")
    exit()

expanded_df = pd.DataFrame(records)

# Группируем по годам и компаниям
grouped = expanded_df.groupby(['Year', 'Company']).size().reset_index(name='Count')
pivot = grouped.pivot(index='Year', columns='Company', values='Count')

# Заполняем пропущенные годы нулями для плавности линий
all_years = pd.DataFrame(index=range(2000, 2027))
pivot = all_years.join(pivot).fillna(0)

# Определяем 10 лидеров по общему количеству проектов
total_counts = pivot.sum().sort_values(ascending=False)
print("\n--- СТАТИСТИКА ПРОЕКТОВ ПО КОМПАНИЯМ (Топ-15) ---")
print(total_counts.head(15))
print("-" * 50)

top_companies = total_counts.head(10).index.tolist()
pivot = pivot[top_companies]

# --- Визуализация ---
fig, ax = plt.subplots(figsize=(18, 9))
fig.patch.set_facecolor('#0F1117')
ax.set_facecolor('#171B28')

# Цветовая палитра
COLORS = {
    "Huawei": "#FF4444",      # Ярко-красный
    "Alibaba": "#FF9900",     # Оранжевый
    "ZTE": "#00CC66",         # Зеленый
    "Tencent": "#00AAFF",     # Голубой
    "ByteDance": "#AA66FF",   # Фиолетовый
    "China Mobile": "#FFEE00", # Желтый
    "Baidu": "#5588FF",       # Синий
    "China Telecom": "#FF55AA", # Розовый
    "Xiaomi": "#FF6600",      # Темно-оранжевый
    "iFLYTEK": "#AAAAAA"      # Серый
}

cmap = plt.get_cmap('tab20')
cdict = {}
for i, c in enumerate(top_companies):
    cdict[c] = COLORS.get(c, cmap(i % 20))

years = pivot.index.tolist()

for company in top_companies:
    counts = pivot[company].values
    color = cdict[company]
    
    # Фон под линиями
    ax.fill_between(years, counts, alpha=0.06, color=color)
    
    # Линии и маркеры
    ax.plot(years, counts, color=color, linewidth=2.8,
            marker='o', markersize=6, markerfacecolor=color,
            markeredgecolor='#0F1117', markeredgewidth=1.5,
            label=f"{company} ({int(total_counts[company])} в сумме)", zorder=5)
            
    # Подписи пиков (где больше или равно 2 проектов в год)
    for i, val in enumerate(counts):
        if val >= 2:
            ax.annotate(
                f"{int(val)}",
                xy=(years[i], val),
                color=color, fontsize=10, fontweight='bold',
                va='bottom', ha='center',
                xytext=(0, 7), textcoords='offset points'
            )

# Значимые события
events = {
    2013: "Belt & Road Initiative",
    2017: "Digital Silk Road Summit",
    2021: "ASEAN 5G Expansion",
    2025: "AI & Data Centers Boom",
}
for yr, label in events.items():
    ax.axvline(yr, color='#FFFFFF', linewidth=0.8, linestyle=':', alpha=0.3)
    # Динамическая высота текста
    y_lim = ax.get_ylim()[1]
    ax.text(yr + 0.2, y_lim * 0.92, label, color='#AAAAAA', fontsize=8.5, va='top')

# Оформление осей
ax.set_xlim(1999.5, 2026.5)
ax.set_ylim(bottom=-0.2)
ax.set_xticks(range(2000, 2027))
ax.set_xticklabels([str(y) for y in range(2000, 2027)], rotation=45, color='#BBBBBB', fontsize=9)

max_val = int(pivot.values.max())
ax.set_yticks(range(0, max_val + 2))
ax.set_yticklabels([str(i) for i in range(0, max_val + 2)], color='#BBBBBB', fontsize=9)

ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
ax.yaxis.grid(True, color='#2A2F42', linewidth=0.8, alpha=0.4, zorder=0)
ax.xaxis.grid(True, color='#1E2236', linewidth=0.5, alpha=0.3, zorder=0)

# Заголовки
ax.set_title('Динамика реализации технологических проектов по компаниям (2000–2026)\nЦифровой Шёлковый путь (Top-10 лидеров)',
             color='#FFFFFF', fontsize=18, fontweight='bold', pad=30)
ax.set_xlabel('Год', color='#888888', fontsize=12, labelpad=15)
ax.set_ylabel('Количество проектов', color='#888888', fontsize=12, labelpad=15)

# Легенда
legend = ax.legend(loc='upper left', frameon=True, facecolor='#1E2236', edgecolor='#2A2F42',
                   labelcolor='#DDDDDD', fontsize=9, title='Компаний холдинги', title_fontsize=11)
legend.get_title().set_color('#888888')

# Подвал
fig.text(0.99, 0.01, 'Источник: авторская база данных ЦШП (145 источников). Группировка по материнским компаниям.',
         ha='right', va='bottom', color='#555577', fontsize=9, style='italic')

plt.tight_layout()
output_filename = 'company_trends_chart.png'
plt.savefig(output_filename, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"\nГрафик успешно создан и сохранен как: {output_filename}")
