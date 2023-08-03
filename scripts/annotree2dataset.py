#!/usr/bin/env python

import argparse
import pandas as pd
import seaborn as sns

from os import path
from pathlib import Path

SELF_PATH = Path(path.abspath(__file__))
GTDB_PATH = path.join(SELF_PATH.parent.parent, 'gtdb/r95')
GTDB_REPS_PATH = path.join(GTDB_PATH, 'metadata_representatives.csv')

ANNOTREE_ID = "gtdb_id"
SIMPLEBAR_HEADER_FORMAT = """
DATASET_SIMPLEBAR
SEPARATOR COMMA
DATASET_LABEL,{label}
COLOR,{hex_color}
DATA
"""



AGG_LEVELS = dict(species='gtdbId', genus='genus', family='family',
                  order='order', class_='class', phylum='phylum')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', '-i', type=str, required=True, dest='input',
                        help='Input annotree hits CSV file.')
    parser.add_argument('--out', '-o', type=str, default='iTOL_dataset.txt',
                        help='Output iTOL dataset file name.')
    parser.add_argument('--label', '-l', type=str, default='annotree',
                        help='iTOL dataset label.')
    parser.add_argument('--palette', '-p', type=str, default='tab10',
                        help='Seaborn palette name for colors.')
    parser.add_argument('--agg_level', '-a', type=str, default='species',
                        help='Aggregation level for annotree hits.')

    args = parser.parse_args()

    print('Reading annotree hits...')
    annotree_df = pd.read_csv(args.input)
    agg_key = AGG_LEVELS[args.agg_level]
    annotree_counts = annotree_df.groupby(agg_key).agg(dict(sequence='count'))
    annotree_counts.columns = ['count']

    # Normalize hit count by number of representative genomes
    if args.agg_level != 'species':
        print('Normalizing hit counts per {0}...'.format(agg_key))
        # Annotree is drawn from GTDB r95.
        # I believe they only annotated the representative genomes.
        reps_df = pd.read_csv(GTDB_REPS_PATH)
        reps_count = reps_df.groupby(agg_key).agg(dict(species='count'))
        reps_count.columns = ['count']
        annotree_counts = annotree_counts / reps_count
        mask = annotree_counts['count'].notnull()
        annotree_counts = annotree_counts[mask]
        annotree_counts.columns = ['normalized_count']

    print(annotree_counts.head(20))
    print('Writing iTOL dataset...')
    pal = sns.color_palette(args.palette)
    header_text = SIMPLEBAR_HEADER_FORMAT.format(
        label=args.label, hex_color=pal.as_hex()[0])
    with open(args.out, 'w') as f:
        f.write(header_text)
        annotree_counts.to_csv(f, header=False)
    
    print('Done!')


if __name__ == '__main__':
    main()
