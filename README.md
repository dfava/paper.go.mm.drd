Daniel S. Fava
danielsf@ifi.uio.no
www.danielfava.com

copyright: CC BY 4.0
https://creativecommons.org/licenses/by/4.0/

See https://github.com/dfava/paper.go.mm.drd

This repository contains code and data that went into creating the figure in the "Memory footprint" subsection of the paper.

### Code

| File | Description |
|:--- |:-------------|
| `src/analysis.ipynb` |  Jupyter notebook used to create the figure from the raw data |
| `src/build.py` | script used to build `sortnp.go` binary with data-race detection enabled |
| `ft.py` | implementation of a reference data-race detector (FastTrack) |
| `race.py` | supporting classes used in `ft.py` |
| `sortnp.go` |  in-place parallel sorting algorithm |
| `test_ft.py` | unit tests for `ft.py` |
| `tsan_patch.diff` | a patch to the TSan library in order to call out to data-race detector ft.py implemented in Python |

### Raw data

```
data/sortnp.ft.out
data/sortnp.fix.ft.out
```
