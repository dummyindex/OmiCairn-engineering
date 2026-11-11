# Third-party notices

## MEBOCOST (`mebocost/`)

The `mebocost/` directory contains a vendored copy of the MEBOCOST source code
(metabolite-mediated cell-cell communication modelling), Copyright (c) 2022
Kaifu Chen Lab, Rongbin Zheng, distributed under the BSD 3-Clause License
(see `mebocost/LICENSE`). Upstream: https://github.com/kaifuchenlab/MEBOCOST

The MEBOCOST **data** (metabolite-sensor database, annotation tables and demo
dataset under `mebocost/data/`) and the upstream demo notebook are **not**
redistributed here, because the upstream "Term of Usage" (see
`mebocost/README.md`) restricts redistribution of the data. To use MEBOCOST,
obtain the `data/` directory from the upstream repository, place it at
`mebocost/data/`, and accept the upstream terms. The relative paths in
`mebocost/src/mebocost.conf` expect that layout.

Please cite the MEBOCOST paper if you use it.
