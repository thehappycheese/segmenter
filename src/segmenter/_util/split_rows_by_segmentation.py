import pandas
import numpy as np
from .check_monotonically_increasing_segments import check_monotonically_increasing_segments

def _check_columns_present(name, df, column_names, df_name):
    if not all(item in df.columns for item in column_names):
        raise ValueError(f"{name} {[column_name for column_name in column_names if column_name not in df.columns]} not in `{df_name}`. Did you mean to use `{df_name}.reset_index(drop=False)`?")


class CN:
    original_index = "original_index"
    original_df_num = "original_df_num"
    additional_index = "additional_index"
    event_measure = "event_measure"
    event_type = "event_type"

def split_rows_by_segmentation(
        original_segmentation:pandas.DataFrame,
        additional_segmentation:pandas.DataFrame,
        categories:list[str],
        measure_slk:tuple[str,str],
        measure_true:tuple[str,str],
        name_original_index:str,
        name_additional_index:str,
    ):
    """
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

    Args:
        original_segmentation:
        additional_segmentation:
        categories: Typically `['road','carriageway']`
        measure_slk: Typically `('slk_from','slk_to')`
        measure_true: Typically `('true_from','true_to')`
        name_original_index: The desired name of the column that will be output into result. The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'original_index'`
        name_additional_index:  The desired name of the column that will be output into result. The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'additional_index'`
    """
    
    if (name_original_index==name_additional_index):
        raise ValueError(f"`name_original_index` and `name_additional_index` cannot be the same: {name_original_index}")

    oseg = (
        original_segmentation
        .reset_index(drop=False)
        .loc[:,[*categories, *measure_slk, *measure_true]]
        .assign(**{
            CN.original_index: lambda df: pandas.RangeIndex(len(df.index)),
            CN.original_df_num:0
        })
        .copy()
    )
    

    aseg = (
        additional_segmentation
        .reset_index(drop=False)
        .loc[:,[*categories, *measure_slk, *measure_true]]
        .assign(**{
            CN.original_index: lambda df: pandas.RangeIndex(len(df.index)),
            CN.original_df_num:1
        })
        .copy()
    )


    _check_columns_present("categories",   oseg, categories,   "original_segmentation")
    _check_columns_present("measure_slk",  oseg, measure_slk,  "original_segmentation")
    _check_columns_present("measure_true", oseg, measure_true, "original_segmentation")
    
    _check_columns_present("categories",   aseg, categories,   "additional_segmentation")
    _check_columns_present("measure_slk",  aseg, measure_slk,  "additional_segmentation")
    _check_columns_present("measure_true", aseg, measure_true, "additional_segmentation")

    # TODO: these checks are expensive, are they strictly needed?
    check_monotonically_increasing_segments(oseg, categories, measure_slk)
    check_monotonically_increasing_segments(aseg, categories, measure_slk)

    # TODO: will cause wierd error if one of the slk/true  from/to are swapped. implement a check.

    from_events = pandas.concat([oseg, aseg])
    from_events[CN.event_measure] = from_events[measure_true[0]]
    from_events = from_events.sort_values([CN.event_measure, CN.original_df_num], ascending=[True, True], kind="stable")
    from_events[CN.event_type] = "from"

    to_events = pandas.concat([oseg, aseg])
    to_events[CN.event_measure] = to_events[measure_true[1]]
    to_events = to_events.sort_values([CN.event_measure, CN.original_df_num], ascending=[True, False], kind="stable")
    to_events[CN.event_type] = "to"

    events = pandas.concat([from_events, to_events]).sort_values([*categories, CN.event_measure, CN.original_index], kind="stable")#.sort_values([*categories,"event_measure"], kind="stable")

    results = []
    for group_index, group in events.groupby(categories):
        segments = []
        index_o = None
        index_a = None
        last_measure = None
        for row_index, row in group.iterrows():
            if not last_measure is None and row[CN.event_measure] - last_measure > 0 and not(index_o is None and index_a is None):
                segments.append([*group_index, last_measure, row[CN.event_measure], index_o, index_a])
            if row[CN.event_type] == "from":
                if row[CN.original_df_num] == 0:
                    index_o = row[CN.original_index]
                else:
                    index_a = row[CN.original_index]
            elif row[CN.event_type] == "to":
                if row[CN.original_df_num] == 0:
                    index_o = None
                else:
                    index_a = None
            last_measure = row[CN.event_measure]
        results += segments

    return pandas.DataFrame(data=results, columns=[*categories, *measure_true, name_original_index, name_additional_index])

