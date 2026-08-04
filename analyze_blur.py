import csv

blur_values = []
with open('calibration/review/inventory.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        blur_values.append(float(row['blur_lap']))

blur_values.sort()
n = len(blur_values)
print(f'Total faces: {n}')
print(f'Min: {blur_values[0]:.1f}')
print(f'Max: {blur_values[-1]:.1f}')
print(f'10th percentile: {blur_values[int(n*0.1)]:.1f}')
print(f'25th percentile: {blur_values[int(n*0.25)]:.1f}')
print(f'50th percentile: {blur_values[int(n*0.5)]:.1f}')
print(f'75th percentile: {blur_values[int(n*0.75)]:.1f}')
print(f'90th percentile: {blur_values[int(n*0.9)]:.1f}')
