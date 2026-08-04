import csv
import numpy as np

# Загрузить сырые blur_lap из инвентаризации
blur_values = []
with open('calibration/review/inventory.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        blur_values.append(float(row['blur_lap']))

blur_values = np.array(blur_values)
blur_values.sort()

n = len(blur_values)
p10 = blur_values[int(n * 0.1)]
p50 = blur_values[int(n * 0.5)]
p90 = blur_values[int(n * 0.9)]

print(f"Raw Laplacian distribution:")
print(f"  p10: {p10:.1f}")
print(f"  p50: {p50:.1f}")
print(f"  p90: {p90:.1f}")

# Текущая нормализация (баг)
def old_blur_score(fm):
    return min(1.0, max(0.0, (fm - 20) / 80))

# Новая нормализация (масштабо-инвариантная)
def new_blur_score(fm):
    # Использовать p10/p90 вместо фиксированных 20/100
    # p10 ~ 50 -> порог "очень размыто"
    # p90 ~ 1600 -> порог "очень резкое"
    return min(1.0, max(0.0, (fm - p10) / (p90 - p10)))

# Проверить на примерах
test_values = [3.0, 50.0, 200.0, 600.0, 1000.0, 2000.0, 5000.0]

print(f"\nOld normalization (fm-20)/80:")
for v in test_values:
    print(f"  blur_lap={v:>7.1f} -> blur_score={old_blur_score(v):.4f}")

print(f"\nNew normalization (fm-p10)/(p90-p10):")
for v in test_values:
    print(f"  blur_lap={v:>7.1f} -> blur_score={new_blur_score(v):.4f}")

# Рекомендованный порог blur_score = 0.25 (25-й перцентиль)
# Для p10=52, p90=1623: порог = p10 + 0.25*(p90-p10) = 52 + 0.25*1571 = 445
# Проверим: blur_score(445) = (445-52)/(1623-52) = 393/1571 = 0.25
threshold = p10 + 0.25 * (p90 - p10)
print(f"\nRecommended blur_lap threshold for blur_score=0.25: {threshold:.1f}")
print(f"blur_score({threshold:.1f}) = {new_blur_score(threshold):.4f}")
