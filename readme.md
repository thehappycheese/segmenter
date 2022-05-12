# Segmenter <!-- omit in toc -->

- [1. Introduction](#1-introduction)
  - [1.1. Related Project `pyroads`](#11-related-project-pyroads)
  - [1.2. Related Project `HS`](#12-related-project-hs)
- [2. Installation](#2-installation)
- [3. Usage](#3-usage)
  - [3.1. `segment_by_categories_and_slk_discontinuities()`](#31-segment_by_categories_and_slk_discontinuities)
    - [3.1.1. Example](#311-example)
  - [3.2. `segment_by_categories_and_slk_true_discontinuities()`](#32-segment_by_categories_and_slk_true_discontinuities)
    - [3.2.1. Args](#321-args)
    - [3.2.2. Returns](#322-returns)
    - [3.2.3. Example](#323-example)
  - [3.3. `split_rows_by_category_to_max_segment_length()`](#33-split_rows_by_category_to_max_segment_length)
    - [3.3.1. Args](#331-args)
    - [3.3.2. Returns](#332-returns)
    - [3.3.3. Example](#333-example)
  - [3.4. `split_rows_by_segmentation()`](#34-split_rows_by_segmentation)
    - [3.4.1. Args](#341-args)
    - [3.4.2. Example](#342-example)

## 1. Introduction

Sometimes road condition data is available at constant intervals (e.g. a
roughness measurement every 10 metres), and must be grouped into larger
intervals. Sometimes observations have has uneven intervals (eg local government
area) and must be split into smaller regular intervals.

This package provides several tools to

1. Identify contiguous sections of data based on
   - categories (eg `road_number`, `carriageway`, `lane`) and a linear measure
     (`slk`)
   - categories (eg `road_number`, `carriageway`, `lane`) and linear measures
     (`slk` and `true`)
2. Rearrange data such that each observation applies to a regularly sized linear
   portion of a road network, with `slk_from`/`slk_to` at nice even multiples of
   the requested segment size (by both splitting/repeating rows and/or merging
   rows).

### 1.1. Related Project `pyroads` 

See also segmentation functions available in `pyroads` project
<https://github.com/shaan-nmb/pyroads>. They are similar, but have subtly
different outputs and are useful for different projects.

### 1.2. Related Project `HS`

This package is a spin-off of the
[HS (Homogeneous Segmentation) python package](https://github.com/thehappycheese/HS).
This is a python version of the original
[R package - also called HS](https://cran.r-project.org/web/packages/HS/index.html).

The aim of the HS package is to segment the road network segments based on the
two things listed below such that each segment can be reasonably represented by
a single characteristic value.

1. Categorical variables (eg `road_number`, `carriageway`, `lane`)
2. One or more road condition variables (eg `roughness`, `rutting`,
   `deflection`, `curvature` etc)

## 2. Installation

You can use the following command to install the latest version from the main
branch

```bash
pip install "https://github.com/thehappycheese/segmenter/zipball/main/"
```

Or check the [releases](https://github.com/thehappycheese/segmenter/releases)
for specific versions.

Uninstall using

```bash
pip uninstall segmenter
```

## 3. Usage


### 3.1. `segment_by_categories_and_slk_discontinuities()`

Used to create the column `seg.ctg` in the example below: (for more details
please see the documentation for
`segment_by_categories_and_slk_true_discontinuities()` below)

#### 3.1.1. Example
```python
import pandas as pd
import numpy as np
from segmenter import segment_by_categories_and_slk_discontinuities

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
actual_result["seg.ctg"] = segment_by_categories_and_slk_discontinuities(
    data_to_segment,
    ["road_no", "carriageway", "xsp"],
    measure_slk =("slk_from", "slk_to"),
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
        ["H001", "L", "L2", 0.080, 0.090, 0.090, 0.110, "d", 2],
        ["H001", "L", "L2", 0.090, 0.100, 0.110, 0.120, "e", 2],

        ["H001", "L", "L3", 0.080, 0.100, 0.070, 0.090, "e", 3], # XSP discontinuity
        ["H001", "L", "L3", 0.100, 0.120, 0.090, 0.110, "f", 3],

        ["H001", "R", "L3", 0.010, 0.050, 0.010, 0.050, "a", 4], # SLK discontinuity (overlap)
        ["H001", "R", "L3", 0.050, 0.070, 0.050, 0.070, "b", 4],
        ["H001", "R", "L3", 0.050, 0.060, 0.070, 0.080, "c", 5],
        ["H001", "R", "L3", 0.060, 0.070, 0.080, 0.100, "d", 5],
        ["H001", "R", "L3", 0.070, 0.090, 0.100, 0.110, "e", 5],
    ]
)

assert actual_result.compare(expected_result).empty
```

### 3.2. `segment_by_categories_and_slk_true_discontinuities()`

Returns a series containing integer segment labels:

A new 'segment' is started whenever one of the `categories` changes or
any time there is a discontinuity in the slk and/or true measure.

Please Note:

- For each unique combination of `categories` in the input `data`, the range `true_from` to `true_to` for observations **must** be non-overlapping.
- No check is made for overlapping observations in this function, it is actually very computationally intensive to do so. I might write a utility that does it one day.
- Weird stuff will happen if there are overlaps
- You have been warned

Internally, data is sorted by the `categories` (in order provided) then by
`measure_true[0]` prior to seeking discontinuities then labeling.

#### 3.2.1. Args

- `data` (`pandas.DataFrame`):
  - data to be segmented
- `categories` (`list[str]`):
  - column names of categories to segment by; eg `["road", "cwy"]` or `["road", "cwy", "xsp"]`
- `measure_slk` (`tuple[str,str]`):
  - column names of slk measure to segment by; eg `("slk_from", "slk_to")`
- `measure_true` (`tuple[str,str]`):
  - column names of true measure to segment by; eg `("true_from", "true_to")`

#### 3.2.2. Returns

`pandas.Series`: A series of integers which label the segment_id of each row. A
series with an index that is compatible with the input `data` such that it can
be easily joined or assigned to the original dataframe.

#### 3.2.3. Example

Used to create the column `seg.ctg` in the example below:

```python
from segmenter import segment_by_categories_and_slk_true_discontinuities

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

### 3.3. `split_rows_by_category_to_max_segment_length()`

Split rows by category, then into segments of even length. The `slk_from` /
`slk_to` of each segment will be at integer multiples of `max_segment_length`.

Other columns in the dataframe are recombined with the output by taking the
values from the single input row which has the largest overlap with the output
row. The result of this recombination may not be ideal; for example

- there is no check regarding missing values; the input row transferred to the
  output may have missing values. You may expect the longest **not-blank**
  value, but that is not what you get.
- there is no check regarding repeated values; you may expect the output to
  reflect the most common **value** when considering the combined length of many
  input rows, but that is not what you will get.

If the above issues are a concern you may wish to drop the value columns and
re-merge them using a different tool.

#### 3.3.1. Args

- `data` (`pandas.DataFrame`):
  - DataFrame to be segmented
- `measure_slk` (`tuple[str,str]`):
  - Column names of slk measure to segment by; eg `("slk_from", "slk_to")`
- `measure_true` (`tuple[str,str]`):
  - Column names of true measure to segment by; eg `("true_from", "true_to")`
- `categories` (`list[str]`):
  - Column names of categories to segment by; eg `["road", "cwy"]`
- `min_segment_length` (`float`, optional): Segments shorter than this will be
  merged with adjacent segments. Only happens to the first and last observation
  in each segment id. Default is Zero.
- `max_segment_length` (`float`):
  - This is the target segment length. For each row in the output
    `max_segment_length == slk_to - slk_from`
  - For each row in the output `slk_from` / `slk_to` will be at integer
    multiples of `max_segment_length` if possible.
  - May not be achieved at
    - the beginning or end of a continuous run of segments (ie a lane or
      carriageway section), or
    - When the segment in the input is already shorter than `max_segment_length`

#### 3.3.2. Returns

`pandas.DataFrame`: Will have the same general column layout except

- `slk_from` / `slk_to` will have been made into regular segment lengths, in integer multiples of `max_segment_length`.
- `true_from` / `true_to` will be adjusted to suit the new slks
- data will have been repeated or merged (as described above) to suit the new number of rows
- `segment_id` column has been added (see documentation for `segment_by_categories_and_slk_true_discontinuities()`)
- `__original_sort_order` column has been added, should you wish to restore the approximate original sort order of the data, since the dataframe is sorted arbitrarily inside the function.

> Note: Original data segmentation is not preserved; effectively data is merged into a continuous segments based on the same logic as `segment_by_categories_and_slk_true_discontinuities`, then split as described above. I consider this to be a problem with the implementation, as in some situations the original segmentation is significant and all that is desired is to split segments longer than the `max_segment_length` argument. Currently this is not possible.

#### 3.3.3. Example

```python
import pandas as pd
import numpy as np
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
        "__original_order",
        "value"
    ],
    data=[
        ["H001", "L", "L1", 0, 0.041, 0.045, 0.041, 0.045, 0, "a"],
        ["H001", "L", "L1", 0, 0.045, 0.050, 0.045, 0.050, 0, "a"],
        ["H001", "L", "L1", 0, 0.050, 0.055, 0.050, 0.055, 1, "b"],
        ["H001", "L", "L1", 0, 0.055, 0.061, 0.055, 0.061, 1, "b"],
        ["H001", "L", "L1", 1, 0.080, 0.085, 0.061, 0.066, 2, "c"], # SLK discontinuity (gap)
        ["H001", "L", "L1", 1, 0.085, 0.090, 0.066, 0.071, 2, "c"],
        ["H001", "L", "L1", 1, 0.090, 0.096, 0.071, 0.077, 3, "d"], # early finish (join)
        
        ["H001", "L", "L2", 2, 0.040, 0.045, 0.040, 0.045, 4, "e"],
        ["H001", "L", "L2", 2, 0.045, 0.050, 0.045, 0.050, 4, "e"],
        ["H001", "L", "L2", 2, 0.050, 0.055, 0.050, 0.055, 5, "f"],
        ["H001", "L", "L2", 2, 0.055, 0.060, 0.055, 0.060, 5, "f"], # TRUE discontinuity (gap) (Note: overlaps not permitted for true)
        ["H001", "L", "L2", 3, 0.060, 0.065, 0.070, 0.075, 6, "g"],
        ["H001", "L", "L2", 3, 0.065, 0.070, 0.075, 0.080, 6, "g"],
        ["H001", "L", "L2", 3, 0.070, 0.075, 0.080, 0.085, 7, "h"],
        ["H001", "L", "L2", 3, 0.075, 0.080, 0.085, 0.090, 7, "h"],

        ["H001", "L", "L3", 4, 0.080, 0.085, 0.080, 0.085, 8, "i"], # XSP discontinuity
        ["H001", "L", "L3", 4, 0.085, 0.090, 0.085, 0.090, 8, "i"],
        ["H001", "L", "L3", 4, 0.090, 0.095, 0.090, 0.095, 9, "j"],
        ["H001", "L", "L3", 4, 0.095, 0.100, 0.095, 0.100, 9, "j"],

        ["H001", "R", "L3", 5, 0.010, 0.015, 0.010, 0.015, 10, "k"],
        ["H001", "R", "L3", 5, 0.015, 0.020, 0.015, 0.020, 10, "k"],
        ["H001", "R", "L3", 5, 0.020, 0.025, 0.020, 0.025, 11, "l"],
        ["H001", "R", "L3", 5, 0.025, 0.030, 0.025, 0.030, 11, "l"], # SLK discontinuity (overlap)
        ["H001", "R", "L3", 6, 0.039, 0.045, 0.030, 0.036, 12, "m"],
        ["H001", "R", "L3", 6, 0.045, 0.050, 0.036, 0.041, 13, "n"],
        ["H001", "R", "L3", 6, 0.050, 0.055, 0.041, 0.046, 13, "n"],

        ["H002", "L", "L1", 7, 0.000, 0.006, 0.000, 0.006, 19, "q"], # Already too small

        ["H002", "R", "L4", 8, 0.000, 0.006, 0.000, 0.006, 16, "t"], # Already too small
    ]
).drop(columns="__original_order")


expected_result = expected_result.set_index(
    ["road_no", "carriageway", "xsp", "segment_index"]
)

pd.testing.assert_frame_equal(
    result,
    expected_result,
    check_like =False, # ignore column order and label order
)
```

### 3.4. `split_rows_by_segmentation()`

Split rows by segmentation.

Combines two segmentations, returning a new dataframe

- The result starts out the same as `original_segmentation`
- rows are split and
- new rows are created
- such that
  - the `result` 100% covers / contains `original_segmentation`
  - the `result` 100% covers / contains `additional_segmentation`
  - segments in `result` do not overlap other segments in `result`
  - all start and end points of segments in `result` can be found in either `original_segmentation` or `additional_segmentation`

#### 3.4.1. Args

- `original_segmentation` (`pandas.DataFrame`):
  - Dataframe to be segmented
- `additional_segmentation` (`pandas.DataFrame`):
  - Dataframe that defines the additional segmentation boundaries to be added to `original_segmentation`
- `categories` (`list[str]`):
  - Column names of categories that define continuous runs of segments in both dataframes. Typically `['road','carriageway']`:
- `measure_slk` (`tuple[str, str]`):
  - Typically `('slk_from','slk_to')`
- `measure_true` (`tuple[str, str]`):
  - Typically `('true_from','true_to')` (can be set to the same values as `measure_slk` if there is no separate true measure)
- `name_original_index` (`str`):
  - The desired name of the column that will be output into result.
  - The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'original_index'`
- `name_additional_index` (`str`):
  - The desired name of the column that will be output into result.
  - The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'additional_index'`

#### 3.4.2. Example

```python
import pandas as pd
import numpy as np
from segmenter import split_rows_by_segmentation

original_segmentation = pd.DataFrame(
    columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value"],
    data=[
        ["H001", "L", "L1", 0.030, 0.040, 0.010, 0.020, "a"],
        ["H001", "L", "L1", 0.040, 0.050, 0.020, 0.030, "b"],
        
        ["H001", "L", "L2", 0.030, 0.045, 0.010, 0.025, "e"],
        ["H001", "L", "L2", 0.045, 0.060, 0.025, 0.040, "f"],

        ["H002", "R", "L4", 0.000, 0.010, 0.000, 0.010, "r"],
        ["H002", "R", "L4", 0.010, 0.030, 0.010, 0.030, "s"],

        ["H002", "R", "L4", 0.050, 0.080, 0.050, 0.080, "t"],
    ]
)

additional_segmentation = pd.DataFrame(
    columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value"],
    data=[
        ["H001", "L", "L1", 0.030, 0.045, 0.010, 0.025, "z"],
        ["H001", "L", "L1", 0.045, 0.055, 0.025, 0.035, "y"],
        
        ["H001", "L", "L2", 0.030, 0.065, 0.010, 0.045, "x"],
        
        ["H002", "R", "L4", 0.005, 0.012, 0.005, 0.012, "w"],
        ["H002", "R", "L4", 0.015, 0.040, 0.015, 0.040, "u"],

        ["H002", "R", "L4", 0.052, 0.080, 0.052, 0.080, "v"],
    ]
)

result = split_rows_by_segmentation(
    original_segmentation   = original_segmentation,
    additional_segmentation = additional_segmentation,
    categories              = ["road_no", "carriageway", "xsp"],
    measure_slk             = ("slk_from", "slk_to"),
    measure_true            = ("true_from", "true_to"),
    name_original_index     = "original_index",
    name_additional_index   = "additional_index",
)

expected_result = pd.DataFrame(
    columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "original_index", "additional_index"],
    data=[
        ["H001", "L", "L1", 0.030, 0.040, 0.010, 0.020,      0,      0],
        ["H001", "L", "L1", 0.040, 0.045, 0.020, 0.025,      1,      0],
        ["H001", "L", "L1", 0.045, 0.050, 0.025, 0.030,      1,      1],
        ["H001", "L", "L1", 0.050, 0.055, 0.030, 0.035, np.nan,      1],
        ["H001", "L", "L2", 0.030, 0.045, 0.010, 0.025,      2,      2],
        ["H001", "L", "L2", 0.045, 0.060, 0.025, 0.040,      3,      2],
        ["H001", "L", "L2", 0.060, 0.065, 0.040, 0.045, np.nan,      2],
        ["H002", "R", "L4", 0.000, 0.005, 0.000, 0.005,      4, np.nan],
        ["H002", "R", "L4", 0.005, 0.010, 0.005, 0.010,      4,      3],
        ["H002", "R", "L4", 0.010, 0.012, 0.010, 0.012,      5,      3],
        ["H002", "R", "L4", 0.012, 0.015, 0.012, 0.015,      5, np.nan],
        ["H002", "R", "L4", 0.015, 0.030, 0.015, 0.030,      5,      4],
        ["H002", "R", "L4", 0.030, 0.040, 0.030, 0.040, np.nan,      4],
        ["H002", "R", "L4", 0.050, 0.052, 0.050, 0.052,      6, np.nan],
        ["H002", "R", "L4", 0.052, 0.080, 0.052, 0.080,      6,      5],
    ]
)

pd.testing.assert_frame_equal(
    result,
    expected_result,
    check_like=False, # ignore column order and label order
)
```
