#!/usr/bin/env python

"""Script to convert AnnoTree hits to iTOL dataset.

TODO: automate legend generation.
TODO: make sure that the AnnoTree tree is using the GTDB taxonomy.
"""

__author__ = 'Avi I. Flamholz'

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

MULTIBAR_HEADER_FORMAT = """
DATASET_SIMPLEBAR
SEPARATOR COMMA
DATASET_LABEL,{label}
COLOR,#ff0000
FIELD_COLORS,{field_colors}
FIELD_LABELS,{field_labels}
DATA
"""

BINARY_HEADER_FORMAT = """
DATASET_BINARY
SEPARATOR COMMA
DATASET_LABEL,{label}
COLOR,#ff0000
FIELD_COLORS,{field_colors}
FIELD_LABELS,{field_labels}
FIELD_SHAPES,{field_shapes}
DATA
"""

AGG_LEVELS = {
    'species': 'gtdbId',
    'genus': 'genus',
    'family': 'family',
    'order': 'order',
    'class': 'class',
    'phylum': 'phylum'
}
 
def count_hits(fh, agg_level, reps_df, presence_absence=False):
    """Count hits in annotree CSV file at this aggregation level.
    
    Args:
        fh (file): File handle to annotree CSV file.
        agg_level (str): Aggregation level to count hits at.
        presence_absence (bool): If True, return presence/absence
            instead of counts.
    
    Returns:
        pd.DataFrame: DataFrame with counts at this aggregation level.
    """
    df = pd.read_csv(fh).set_index('gtdbId')

    # Since AnnoTree does not alway output phylogenetic information
    # we have to fetch it from the reference genomes in case it is missing.
    agg_key = AGG_LEVELS[agg_level]
    df[agg_key] = reps_df.loc[df.index][agg_key]

    counts = df.groupby(agg_key).agg(dict(sequence='count'))
    if presence_absence:
        counts = (counts > 0).astype(int)
    counts.columns = ['count']
    return counts


def normalize_counts(counts, agg_level, reps_df):
    """Normalize hit counts by number of representative genomes.
    
    Args:
        counts (pd.DataFrame): DataFrame with counts at this aggregation level.
        agg_level (str): Aggregation level to normalize counts at.
        reps_df (pd.DataFrame): DataFrame with representative genome taxonomy.
    
    Returns:
        pd.DataFrame: DataFrame with normalized counts at this aggregation level.
    """
    # No normalization needed for species level
    if agg_level == 'species':
        return counts
    
    # Count number of representative genomes at this aggregation level
    reps_count = reps_df.groupby(agg_level).agg(dict(species='count'))
    reps_count.columns = ['count']

    # Normalize counts by number of representative genomes
    normed = counts / reps_count
    mask = normed['count'].notnull()

    # Drop rows with no data.
    return normed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', '-i', type=argparse.FileType('r'), nargs='+',
                        required=True, dest='input',
                        help='Input annotree hits CSV file path(s).')
    parser.add_argument('--labels', '-l', type=str, nargs='+',
                        default=('annotree',),
                        help='Labels for each file in order.')
    parser.add_argument('--out', '-o', type=str, default='iTOL_dataset.txt',
                        help='Output iTOL dataset file name.')
    parser.add_argument('--palette', '-p', type=str, default='tab10',
                        help='Seaborn palette name for colors.')
    parser.add_argument('--agg_level', '-a', type=str, default='species',
                        help='Aggregation level for annotree hits.',
                        choices=sorted(AGG_LEVELS.values()))
    parser.add_argument('--plot_type', '-t', type=str, default='bar',
                        help='iTOL plot type.',
                        choices=('bar', 'binary'))
    parser.add_argument('--presence_absence', action="store_true", default=False, 
                        help='Use presence/absence instead of counts. Recommended for binary plots.')
    parser.add_argument('--binary_threshold', '-b', type=float, default=0.5,
                        help='Threshold for binarizing counts or normalized counts.')
    
    args = parser.parse_args()
    msg = 'Number of labels must match number of input files.'
    assert len(args.input) == len(args.labels), msg

    if args.presence_absence and args.plot_type != 'binary':
        print('WARNING: presence/absence is only recommended for binary plots.')

    print('Reading annotree hits...')
    reps_df = pd.read_csv(GTDB_REPS_PATH).set_index('accession')

    count_cols = []
    for label,fh in zip(args.labels, args.input):
        print('Input file {0} with label {1}'.format(fh.name, label))
        counts = count_hits(fh, args.agg_level, reps_df, args.presence_absence)
        normed = normalize_counts(counts, args.agg_level, reps_df)
        normed.columns = [label]
        count_cols.append(normed)
    annotree_counts = pd.concat(count_cols, axis=1)
    annotree_counts = annotree_counts.dropna(axis=0, how='all')

    # If they provided the same label to multiple files, sum them.
    annotree_counts = annotree_counts.fillna(0).groupby(
        annotree_counts.columns, axis=1).sum()
    if args.presence_absence:
        annotree_counts = (annotree_counts > 0).astype(int)

    print('Aggregating counts...')
    labels = annotree_counts.columns.tolist()
    n_colors = len(labels)
    pal = sns.color_palette(args.palette, n_colors=n_colors)
    hex_colors = pal.as_hex()

    header_text = ''
    if args.plot_type == 'binary':
        print('Binarizing counts...')
        field_colors = ','.join(hex_colors)
        field_labels = ','.join(labels)
        field_shapes = ','.join(['1' for _ in range(n_colors)])
        header_text = BINARY_HEADER_FORMAT.format(
            label='annotree', field_colors=field_colors,
            field_labels=field_labels, field_shapes=field_shapes)
        annotree_counts = (annotree_counts > args.binary_threshold).astype(int)
    elif args.plot_type == 'bar' and n_colors > 1: 
        field_colors = ','.join(hex_colors)
        field_labels = ','.join(labels)
        header_text = MULTIBAR_HEADER_FORMAT.format(
            label='annotree', field_colors=field_colors,
            field_labels=field_labels)
    else:
        header_text = SIMPLEBAR_HEADER_FORMAT.format(
            label=args.labels[0], hex_color=hex_colors[0])
    
    print('Writing iTOL dataset...')
    with open(args.out, 'w') as f:
        f.write(header_text)
        annotree_counts.to_csv(f, header=False)
    
    print('Done!')


if __name__ == '__main__':
    main()
