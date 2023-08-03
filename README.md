# annotree2itol
Scripts for moving AnnoTree annotations to iTOL

## Introduction

[AnnoTree](http://annotree.uwaterloo.ca/) is a useful resource for inspecting the presence or absence of protein families on a phylogenetic tree. However, it is cumbersome to customize AnnoTree output for publication figures, which are often made with [iTOL](https://itol.embl.de/upload.cgi) -- the Interactive Tree of Life. This repository provides scripts for converting AnnoTree output into iTOL input. 

## Steps

1. Load AnnoTree and download results for the queries of your choosing. 

AnnoTree supports various types of queries, including KEGG IDs (e.g., K00370 for NarG) or PFAMs (e.g., PF00092 for the von Willebrand factor type A). After your results load, click the "All query results" button to download the file. The file will be named "annotree_hits.csv" so definitely rename it so you remember what you searched for. See `data/080323_CAs/K01673_beta_CA.csv` for example.

2. Download the AnnoTree tree file at the desired resolution.

On the top left of the AnnoTree results page, you can select a phylogenetic resolution like "class" or "phylum." Once you select the resolution, click the "Newick" button on the right to download the tree in Newick format. The file will be named "tree_of_life.newick" so definitely rename it. See `data/080323_CAs/tree_phylum_level.newick` for example. 

3. Run the script to generate an iTOL dataset from your annotree data. 

The script `scripts/annotree2dataset.py` will collect all your AnnoTree data, aggregate it at the desired level, and output a "dataset" file that can be uploaded to iTOL. For now it only makes bar plots and binary presence/absence diagrams. You can run the script with `-h` to learn all the options. 

```console
$ python scripts/annotree2dataset.py -h 
usage: annotree2dataset.py [-h] --in INPUT [INPUT ...] [--labels LABELS [LABELS ...]] [--out OUT] [--palette PALETTE] [--agg_level {class,family,genus,gtdbId,order,phylum}] [--plot_type {bar,binary}]
                           [--presence_absence] [--binary_threshold BINARY_THRESHOLD]

optional arguments:
  -h, --help            show this help message and exit
  --in INPUT [INPUT ...], -i INPUT [INPUT ...]
                        Input annotree hits CSV file path(s).
  --labels LABELS [LABELS ...], -l LABELS [LABELS ...]
                        Labels for each file in order.
  --out OUT, -o OUT     Output iTOL dataset file name.
  --palette PALETTE, -p PALETTE
                        Seaborn palette name for colors.
  --agg_level {class,family,genus,gtdbId,order,phylum}, -a {class,family,genus,gtdbId,order,phylum}
                        Aggregation level for annotree hits.
  --plot_type {bar,binary}, -t {bar,binary}
                        iTOL plot type.
  --presence_absence    Use presence/absence instead of counts. Recommended for binary plots.
  --binary_threshold BINARY_THRESHOLD, -b BINARY_THRESHOLD
                        Threshold for binarizing counts or normalized counts.
```

I've included example data in the repository so that you can run the script yourself. If you run this commond from the repository root directory, it will generate a dataset marking the presence or absence of several genes at the phylum level. 

```console
$ python scripts/annotree2dataset.py -i data/080323_CAs/K01672_alpha_CA.csv \
    data/080323_CAs/K01673_beta_CA.csv data/080323_CAs/K01674_alpha_CA.csv \
    data/080323_CAs/PF05982_sbtA.csv data/080323_CAs/PF10070_DabA.csv \
    -l alphaCA betaCA alphaCA sbtA DabA \
    -a phylum -t binary --presence_absence -o my_iTOL_dataset.txt
```

Notice that the `-o` option indicates that we are saving output to a file of our choosing. Feel free to change this option. 

4. Upload the Newick tree file to [iTOL](https://itol.embl.de/upload.cgi).

5. Upload the generated dataset to annotate your tree.

In iTOL, open the Datasets tab and click "Upload annotation files" to upload the generated file. Some errors may pop up related to iTOL being unable to find some groups of organisms on the tree, but your graph will also appear. At least at the phylum level, the missing groups are ones with very few representative genomes. I suspect AnnoTree pruned these from its tree. 

6. Customize your tree on iTOL.

7. Success! 
