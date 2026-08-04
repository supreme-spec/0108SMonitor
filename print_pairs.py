"""Print pairs for ceiling/ir_screen"""
import csv

with open('calibration/out/pairs.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if 'ceiling' in row['folder'] or 'ir_screen' in row['folder']:
            print(f"{row['folder']}/{row['a']} vs {row['folder']}/{row['b']}: {row['cos']}")
