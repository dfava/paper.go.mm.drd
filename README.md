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
| `tsan_patch.diff` | a patch to the TSan library in order to call out to data-race detector `ft.py` implemented in Python |

### Raw data

```
data/sortnp.ft.out
data/sortnp.fix.ft.out
```

### Re-generating the data 

To generate data before the fix.

- Clone LLVM
- Apply patch `tsan_patch.diff` to TSan
- Build TSan Go library file `race_<OS>_<PLATFORM>_.syso`
- Copy library file to `` `go env GOTOOLDIR`/../../../src/runtime/race``
- Compile `sortnp.go` (potentially using `build.py`)
- Run `sortnp.go` setting PYTHONPATH to the location of `ft.py`

To generate data after the fix.

- Having checked-out LLVM and applied patch `tsan_patch.diff` to TSan, modify line `#define RD 0` in `tsan_go.cpp` so it reads `#define RD FT`
- Rebuild TSan Go library file
- Clone Go
- Apply [this patch](https://go-review.googlesource.com/c/go/+/220419/) to Go
- Assuming Go's clone path is `go.git`, copy TSan Go library file to `go.git/src/runtime/race`
- Build Go
- Compile `sortnp.go` using the modified Go (can pass a version of Go to `build.py` script)
- Run `sortnp.go` setting PYTHONPATH to the location of `ft.py`
