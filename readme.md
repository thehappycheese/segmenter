# Segmenter <!-- omit in toc -->

- [1. Introduction](#1-introduction)
	- [1.1. HS Sub-Package](#11-hs-sub-package)
- [2. Installation](#2-installation)
- [3. Usage](#3-usage)
	- [3.1. Segmenter Functions](#31-segmenter-functions)
		- [3.1.1. `segment_by_categories_and_slk_true_discontinuities()`](#311-segment_by_categories_and_slk_true_discontinuities)
		- [3.1.2. `split_rows_by_category_to_max_segment_length()`](#312-split_rows_by_category_to_max_segment_length)
	- [3.2. Homogenous Segmentation](#32-homogenous-segmentation)

## 1. Introduction

Sometimes road condition data is available at constant intervals (e.g. a
roughness measurement every 10 metres), and must be grouped into larger
intervals. Sometimes observations have has uneven intervals (eg local government
area) and must be split into smaller regular intervals.

Several tools to reshape data where each observation applies to a linear portion
(of variable length) of a road network, perhaps distinguishing carriageways and
lanes. Segmentation may mean splitting observations (repeating rows) or
sometimes merging observations to achieve observations that refer to regular
lengths of the road network.

### 1.1. HS Sub-Package

This package currently contains part of an R packaged called HS which has been
copied from the original python port here <https://github.com/thehappycheese/HS>
which was in turn ported from an
[R package - also called HS](https://cran.r-project.org/web/packages/HS/index.html).

The aim of the HS package is to segmentthe road network segments based
on the two things listed below such that each segment can be reasonably represented by a single characteristic value.

1. Categorical variables (eg `road_number`, `carriageway`, `lane`)
2. One or more road condition variables (eg `roughness`, `rutting`, `deflection`, `curvature` etc)



The author of the original R package is **Yongze Song**, and it is related to the following paper:

> Song, Yongze, Peng Wu, Daniel Gilmore, and Qindong Li. "[A spatial heterogeneity-based segmentation model for analyzing road deterioration network data in multi-scale infrastructure systems.](https://ieeexplore.ieee.org/document/9123684)" IEEE Transactions on Intelligent Transportation Systems (2020).

These functions may be removed at a later date in favour of maintaining the
python port repo <https://github.com/thehappycheese/HS>. I want to make upgrades
to the interface of the HS project, but I don't want to do much more on the repo
since it is currently a "faithful" port to python. For now some functionality
has been moved over to this package so I could add a better interface.

## 2. Installation

You can use the following command to install the latest version from the main
branch

```bash
pip install git+https://github.com/thehappycheese/segmenter.git#egg=segmenter
```

Or check the [releases](https://github.com/thehappycheese/segmenter/releases) for specific versions.

Uninstall using

```bash
pip uninstall HS
```

## 3. Usage

### 3.1. Segmenter Functions

#### 3.1.1. `segment_by_categories_and_slk_true_discontinuities()`

```python
from segmenter import segment_by_categories_and_slk_true_discontinuities
# discontinuity at SLK 
data_to_segment = pd.DataFrame(
	columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value"],
	data=[
		["H001", "L", "L1", 0.010, 0.050, 0.010, 0.050, "a"], # SLK discontinuity (gap)
		["H001", "L", "L1", 0.050, 0.070, 0.050, 0.070, "b"],
		["H001", "L", "L1", 0.080, 0.100, 0.070, 0.090, "c"],
		["H001", "L", "L1", 0.100, 0.120, 0.090, 0.110, "d"],

		["H001", "L", "L2", 0.010, 0.050, 0.010, 0.050, "a"], # TRUE discontinuity (gap, overlaps not permitted for true)
		["H001", "L", "L2", 0.050, 0.070, 0.050, 0.070, "b"],
		["H001", "L", "L2", 0.070, 0.080, 0.070, 0.080, "c"],
		["H001", "L", "L2", 0.080, 0.090, 0.090, 0.110, "d"],
		["H001", "L", "L2", 0.090, 0.100, 0.110, 0.120, "e"],

		["H001", "L", "L3", 0.080, 0.100, 0.070, 0.090, "e"], # XSP discontinuity
		["H001", "L", "L3", 0.100, 0.120, 0.090, 0.110, "f"],

		["H001", "R", "L3", 0.010, 0.050, 0.010, 0.050, "a"], # SLK discontinuity (overlap)
		["H001", "R", "L3", 0.050, 0.070, 0.050, 0.070, "b"],
		["H001", "R", "L3", 0.050, 0.060, 0.070, 0.080, "c"],
		["H001", "R", "L3", 0.060, 0.070, 0.080, 0.100, "d"],
		["H001", "R", "L3", 0.070, 0.090, 0.100, 0.110, "e"],
	]
)

actual_result = data_to_segment.copy()
actual_result["seg.ctg"] = segment_by_categories_and_slk_true_discontinuities(
	data_to_segment,
	["road_no", "carriageway", "xsp"],
	measure_slk =("slk_from", "slk_to"),
	measure_true=("true_from","true_to")
)

expected_result = pd.DataFrame(
	columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value" , "seg.ctg"],
	data=[
		["H001", "L", "L1", 0.010, 0.050, 0.010, 0.050, "a", 0], # SLK discontinuity (gap)
		["H001", "L", "L1", 0.050, 0.070, 0.050, 0.070, "b", 0],
		["H001", "L", "L1", 0.080, 0.100, 0.070, 0.090, "c", 1],
		["H001", "L", "L1", 0.100, 0.120, 0.090, 0.110, "d", 1],

		["H001", "L", "L2", 0.010, 0.050, 0.010, 0.050, "a", 2], # TRUE discontinuity (gap, overlaps not permitted for true)
		["H001", "L", "L2", 0.050, 0.070, 0.050, 0.070, "b", 2],
		["H001", "L", "L2", 0.070, 0.080, 0.070, 0.080, "c", 2],
		["H001", "L", "L2", 0.080, 0.090, 0.090, 0.110, "d", 3],
		["H001", "L", "L2", 0.090, 0.100, 0.110, 0.120, "e", 3],

		["H001", "L", "L3", 0.080, 0.100, 0.070, 0.090, "e", 4], # XSP discontinuity
		["H001", "L", "L3", 0.100, 0.120, 0.090, 0.110, "f", 4],

		["H001", "R", "L3", 0.010, 0.050, 0.010, 0.050, "a", 5], # SLK discontinuity (overlap)
		["H001", "R", "L3", 0.050, 0.070, 0.050, 0.070, "b", 5],
		["H001", "R", "L3", 0.050, 0.060, 0.070, 0.080, "c", 6],
		["H001", "R", "L3", 0.060, 0.070, 0.080, 0.100, "d", 6],
		["H001", "R", "L3", 0.070, 0.090, 0.100, 0.110, "e", 6],
	]
)

assert actual_result.compare(expected_result).empty
```

#### 3.1.2. `split_rows_by_category_to_max_segment_length()`

```python
from segmenter import split_rows_by_category_to_max_segment_length
    
    data_to_segment = pd.DataFrame(
        columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value"],
        data=[
            ["H001", "L", "L1", 0.041, 0.050, 0.041, 0.050, "a"], # late start (no join)
            ["H001", "L", "L1", 0.050, 0.061, 0.050, 0.061, "b"], # SLK discontinuity (gap)
            ["H001", "L", "L1", 0.080, 0.090, 0.061, 0.071, "c"],
            ["H001", "L", "L1", 0.090, 0.096, 0.071, 0.077, "d"], # early finish (join)
            
            ["H001", "L", "L2", 0.040, 0.050, 0.040, 0.050, "e"],
            ["H001", "L", "L2", 0.050, 0.060, 0.050, 0.060, "f"], # TRUE discontinuity (gap) (Note: overlaps not permitted for true)
            ["H001", "L", "L2", 0.060, 0.070, 0.070, 0.080, "g"],
            ["H001", "L", "L2", 0.070, 0.080, 0.080, 0.090, "h"],

            ["H001", "L", "L3", 0.080, 0.090, 0.080, 0.090, "i"], # XSP discontinuity
            ["H001", "L", "L3", 0.090, 0.100, 0.090, 0.100, "j"],

            ["H001", "R", "L3", 0.010, 0.020, 0.010, 0.020, "k"], # SLK discontinuity (overlap)
            ["H001", "R", "L3", 0.020, 0.030, 0.020, 0.030, "l"],
            ["H001", "R", "L3", 0.039, 0.045, 0.030, 0.036, "m"], # late finish (join)
            ["H001", "R", "L3", 0.045, 0.055, 0.036, 0.046, "n"],

            ["H002", "R", "L4", 0.000, 0.001, 0.000, 0.001, "r"], # Already too small
            ["H002", "R", "L4", 0.001, 0.003, 0.001, 0.003, "s"],
            ["H002", "R", "L4", 0.003, 0.006, 0.003, 0.006, "t"],

            ["H002", "L", "L1", 0.000, 0.001, 0.000, 0.001, "o"], # Already too small
            ["H002", "L", "L1", 0.001, 0.003, 0.001, 0.003, "p"],
            ["H002", "L", "L1", 0.003, 0.006, 0.003, 0.006, "q"],

        ]
    )

    result = split_rows_by_category_to_max_segment_length(
        data=data_to_segment,
        categories=["road_no", "carriageway", "xsp"],
        measure_slk =("slk_from", "slk_to"),
        measure_true=("true_from","true_to"),
        max_segment_length=0.005,
        min_segment_length=0.002,
    )

    expected_result = pd.DataFrame(
        columns=[
            "road_no",
            "carriageway",
            "xsp",
            "segment_index",
            "slk_from",
            "slk_to",
            "true_from",
            "true_to",
            "value"
        ],
        data=[
            ["H001", "L", "L1", 0, 0.041, 0.045, 0.041, 0.045, "a"],
            ["H001", "L", "L1", 0, 0.045, 0.050, 0.045, 0.050, "a"],
            ["H001", "L", "L1", 0, 0.050, 0.055, 0.050, 0.055, "b"],
            ["H001", "L", "L1", 0, 0.055, 0.061, 0.055, 0.061, "b"],
            ["H001", "L", "L1", 1, 0.080, 0.085, 0.061, 0.066, "c"], # SLK discontinuity (gap)
            ["H001", "L", "L1", 1, 0.085, 0.090, 0.066, 0.071, "c"],
            ["H001", "L", "L1", 1, 0.090, 0.096, 0.071, 0.077, "d"], # early finish (join)
            
            ["H001", "L", "L2", 2, 0.040, 0.045, 0.040, 0.045, "e"],
            ["H001", "L", "L2", 2, 0.045, 0.050, 0.045, 0.050, "e"],
            ["H001", "L", "L2", 2, 0.050, 0.055, 0.050, 0.055, "f"],
            ["H001", "L", "L2", 2, 0.055, 0.060, 0.055, 0.060, "f"], # TRUE discontinuity (gap) (Note: overlaps not permitted for true)
            ["H001", "L", "L2", 3, 0.060, 0.065, 0.070, 0.075, "g"],
            ["H001", "L", "L2", 3, 0.065, 0.070, 0.075, 0.080, "g"],
            ["H001", "L", "L2", 3, 0.070, 0.075, 0.080, 0.085, "h"],
            ["H001", "L", "L2", 3, 0.075, 0.080, 0.085, 0.090, "h"],

            ["H001", "L", "L3", 4, 0.080, 0.085, 0.080, 0.085, "i"], # XSP discontinuity
            ["H001", "L", "L3", 4, 0.085, 0.090, 0.085, 0.090, "i"],
            ["H001", "L", "L3", 4, 0.090, 0.095, 0.090, 0.095, "j"],
            ["H001", "L", "L3", 4, 0.095, 0.100, 0.095, 0.100, "j"],

            ["H001", "R", "L3", 5, 0.010, 0.015, 0.010, 0.015, "k"],
            ["H001", "R", "L3", 5, 0.015, 0.020, 0.015, 0.020, "k"],
            ["H001", "R", "L3", 5, 0.020, 0.025, 0.020, 0.025, "l"],
            ["H001", "R", "L3", 5, 0.025, 0.030, 0.025, 0.030, "l"], # SLK discontinuity (overlap)
            ["H001", "R", "L3", 6, 0.039, 0.045, 0.030, 0.036, "m"],
            ["H001", "R", "L3", 6, 0.045, 0.050, 0.036, 0.041, "n"],
            ["H001", "R", "L3", 6, 0.050, 0.055, 0.041, 0.046, "n"],

            ["H002", "L", "L1", 7, 0.000, 0.006, 0.000, 0.006, "q"], # Already too small

            ["H002", "R", "L4", 8, 0.000, 0.006, 0.000, 0.006, "t"], # Already too small
        ]
    ).set_index(
        ["road_no", "carriageway", "xsp", "segment_index"]
    )

    pd.testing.assert_frame_equal(
        result,
        expected_result,
        check_like =False, # ignore column order and label order
    )
```

### 3.2. Homogenous Segmentation

```python
from HS.homogeneous_segmentation import homogenous_segmentation
import pandas as pd
from io import StringIO

data = """road,slk_from,slk_to,cwy,deflection,dirn
H001,0.00,0.01,L,179.37,L
H001,0.01,0.02,L,177.12,L
H001,0.02,0.03,L,179.06,L
H001,0.03,0.04,L,212.65,L
H001,0.04,0.05,L,175.35,L
H001,0.05,0.06,L,188.66,L
H001,0.06,0.07,L,188.31,L
H001,0.07,0.08,L,174.48,L
H001,0.08,0.09,L,210.28,L
H001,0.09,0.10,L,260.05,L
H001,0.10,0.11,L,228.83,L
H001,0.11,0.12,L,226.33,L
H001,0.12,0.13,L,245.53,L
H001,0.13,0.14,L,315.77,L
H001,0.14,0.15,L,373.86,L
H001,0.15,0.16,L,333.56,L"""


expected_output = """road,slk_from,slk_to,cwy,deflection,dirn,length,seg.id,seg.point
H001,0.00,0.01,L,179.37,L,0.01,1,1
H001,0.01,0.02,L,177.12,L,0.01,1,0
H001,0.02,0.03,L,179.06,L,0.01,1,0
H001,0.03,0.04,L,212.65,L,0.01,1,0
H001,0.04,0.05,L,175.35,L,0.01,2,1
H001,0.05,0.06,L,188.66,L,0.01,2,0
H001,0.06,0.07,L,188.31,L,0.01,2,0
H001,0.07,0.08,L,174.48,L,0.01,2,0
H001,0.08,0.09,L,210.28,L,0.01,2,0
H001,0.09,0.10,L,260.05,L,0.01,3,1
H001,0.10,0.11,L,228.83,L,0.01,3,0
H001,0.11,0.12,L,226.33,L,0.01,3,0
H001,0.12,0.13,L,245.53,L,0.01,3,0
H001,0.13,0.14,L,315.77,L,0.01,3,0
H001,0.14,0.15,L,373.86,L,0.01,3,0
H001,0.15,0.16,L,333.56,L,0.01,3,0
"""

def test_readme_example():
	df = pd.read_csv(StringIO(data))

	df = homogenous_segmentation(
		data                        =df,
		method                      ="shs",
		measure_start               ="slk_from",
		measure_end                 ="slk_to",
		variables                   =["deflection"],
		allowed_segment_length_range=(0.030, 0.080)
	)

	df_expected = pd.read_csv(StringIO(expected_output))

	assert df.compare(df_expected).empty

	assert (df.groupby("seg.id")["length"].sum() >= 0.030).all()
	assert (df.groupby("seg.id")["length"].sum() <= 0.080).all()
```