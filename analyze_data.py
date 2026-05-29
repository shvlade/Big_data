
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import re

# =========================================
# НАСТРОЙКИ
# =========================================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.style.use('seaborn-v0_8-whitegrid')

school_results = {}
spo_results = {}

# =========================================
# ПОИСК EXCEL
# =========================================
files = [
    f for f in glob.glob('*20*.xls*')
    if '~$' not in f
]

school_files = [
    f for f in files
    if 'СПО' not in f and 'СВОД' not in f
]

spo_files = [
    f for f in files
    if 'СПО' in f
]

# =========================================
# ПРЕОБРАЗОВАНИЕ В ЧИСЛО
# =========================================
def to_int(value):

    try:

        if pd.isna(value):
            return 0

        value = (
            str(value)
            .replace(' ', '')
            .replace(',', '.')
        )

        return int(float(value))

    except:
        return 0

# =========================================
# ОБРАБОТКА ШКОЛ
# =========================================
for file in school_files:

    try:

        year = int(
            re.search(r'20\d{2}', file).group()
        )

        excel = pd.ExcelFile(file)

        sheet = next(
            (
                s for s in excel.sheet_names
                if '2.1.1' in s
            ),
            None
        )

        if not sheet:
            continue

        df = pd.read_excel(
            file,
            sheet_name=sheet,
            header=None
        )

        col_9 = None
        col_10 = None

        # -----------------------------
        # ПОИСК КОЛОНОК
        # -----------------------------
        for r in range(min(40, df.shape[0])):

            for c in range(min(40, df.shape[1])):

                text = str(df.iloc[r, c]).strip().lower()

                if text == '9-й класс':
                    col_9 = c

                elif text == '10-й класс':
                    col_10 = c

            if col_9 is not None and col_10 is not None:
                break

        if col_9 is None or col_10 is None:
            continue

        # -----------------------------
        # ПОИСК СТРОКИ
        # -----------------------------
        target_row = None

        for r in range(min(60, df.shape[0])):

            text = str(df.iloc[r, 0]).strip().lower()

            if (
                'в них обучающихся (сумма строк' in text
                or 'всего обучающихся' in text
            ):

                target_row = r
                break

        # запасной вариант
        if target_row is None:

            for r in range(min(60, df.shape[0])):

                text = str(df.iloc[r, 0])

                if 'Итого классов' in text:

                    target_row = r + 1
                    break

        if target_row is None:
            continue

        school_results[year] = {
            '9_grade': to_int(
                df.iloc[target_row, col_9]
            ),
            '10_grade': to_int(
                df.iloc[target_row, col_10]
            )
        }

        print(
            f'{year}: '
            f'9 класс = {school_results[year]["9_grade"]}, '
            f'10 класс = {school_results[year]["10_grade"]}'
        )

    except Exception as e:

        print(f'Ошибка {file}: {e}')

# =========================================
# ОБРАБОТКА СПО
# =========================================
for file in spo_files:

    try:

        year = int(
            re.search(r'20\d{2}', file).group()
        )

        excel = pd.ExcelFile(file)

        sheet = next(
            (
                s for s in excel.sheet_names
                if '2.1.1' in s or '2_1_1' in s
            ),
            None
        )

        if not sheet:
            continue

        df = pd.read_excel(
            file,
            sheet_name=sheet,
            header=None
        )

        spo_value = 0

        for r in range(min(80, df.shape[0])):

            text = str(df.iloc[r, 0]).strip().lower()

            if (
                'основного общего образования – всего' in text
                or 'основного общего образования - всего' in text
            ):

                spo_value = to_int(df.iloc[r, 5])
                break

        spo_results[year] = spo_value

        print(f'{year}: СПО = {spo_value}')

    except Exception as e:

        print(f'Ошибка СПО {file}: {e}')

# =========================================
# DATAFRAME
# =========================================
years = sorted(school_results.keys())

rows = []

for i, year in enumerate(years):

    prev_9 = np.nan

    if i > 0:

        prev_9 = school_results[
            years[i - 1]
        ]['9_grade']

    current_10 = school_results[
        year
    ]['10_grade']

    current_spo = spo_results.get(year, 0)

    pct_10 = (
        current_10 / prev_9 * 100
        if prev_9 == prev_9 and prev_9 > 0
        else np.nan
    )

    pct_spo = (
        current_spo / prev_9 * 100
        if prev_9 == prev_9 and prev_9 > 0
        else np.nan
    )

    rows.append({
        'Year': year,
        '9_prev': prev_9,
        '10_current': current_10,
        'spo_current': current_spo,
        'pct_10': pct_10,
        'pct_spo': pct_spo
    })

stats = pd.DataFrame(rows)

# =========================================
# ФИЛЬТР С 2019
# =========================================
stats = stats[
    stats['Year'] >= 2019
]

# =========================================
# CSV
# =========================================
stats.to_csv(
    'education_statistics.csv',
    index=False,
    encoding='utf-8-sig'
)

print('\nDATAFRAME:')
print(stats)

# =========================================
# ГРАФИК
# =========================================
fig, ax = plt.subplots(
    figsize=(14, 8)
)

valid = stats.dropna()

# новые цвета
blue = '#1565C0'
orange = '#F57C00'

# линия 10 класса
ax.plot(
    valid['Year'],
    valid['pct_10'],
    marker='o',
    markersize=9,
    linewidth=3,
    color=blue,
    label='Переход в 10 класс'
)

# линия СПО
ax.plot(
    valid['Year'],
    valid['pct_spo'],
    marker='D',
    markersize=8,
    linewidth=3,
    color=orange,
    label='Поступление в СПО'
)

# подписи процентов
for _, row in valid.iterrows():

    ax.text(
        row['Year'],
        row['pct_10'] + 1.5,
        f'{row["pct_10"]:.1f}%',
        ha='center',
        fontsize=10,
        color=blue
    )

    ax.text(
        row['Year'],
        row['pct_spo'] + 1.5,
        f'{row["pct_spo"]:.1f}%',
        ha='center',
        fontsize=10,
        color=orange
    )

# оформление
ax.set_title(
    'Траектории выпускников 9-х классов',
    fontsize=18,
    fontweight='bold'
)

ax.set_xlabel(
    'Год поступления',
    fontsize=12
)

ax.set_ylabel(
    'Доля выпускников (%)',
    fontsize=12
)

ax.set_ylim(0, 100)

ax.grid(
    True,
    linestyle='--',
    alpha=0.5
)

ax.legend(
    fontsize=11
)

plt.tight_layout()

# =========================================
# PNG
# =========================================
plt.savefig(
    'education_trajectories.png',
    dpi=300,
    bbox_inches='tight'
)

print('\nСохранено:')
print('education_statistics.csv')
print('education_trajectories.png')

