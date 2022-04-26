import pandas
import numpy as np
from .check_monotonically_increasing_segments import check_monotonically_increasing_segments

def _check_column_present(name, df, column_names, df_name):
    if not all(item in df.columns for item in column_names):
        raise ValueError(f"{name} {[column_name for column_name in column_names if column_name not in df.columns]} not in `{df_name}`. Did you mean to use `{df_name}.reset_index(drop=False)`?")




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
    
    _check_column_present("categories",   original_segmentation, categories,   "original_segmentation")
    _check_column_present("measure_slk",  original_segmentation, measure_slk,  "original_segmentation")
    _check_column_present("measure_true", original_segmentation, measure_true, "original_segmentation")
    
    _check_column_present("categories",   additional_segmentation, categories,   "additional_segmentation")
    _check_column_present("measure_slk",  additional_segmentation, measure_slk,  "additional_segmentation")
    _check_column_present("measure_true", additional_segmentation, measure_true, "additional_segmentation")

    if name_original_index in original_segmentation.columns:
        raise ValueError(f"name_original_index '{name_original_index}' already in original_segmentation")
    if name_additional_index in original_segmentation.columns:
        raise ValueError(f"name_additional_index '{name_additional_index}' already in original_segmentation")

    check_monotonically_increasing_segments(original_segmentation, categories, measure_slk)
    check_monotonically_increasing_segments(additional_segmentation, categories, measure_slk)

    result = (
        original_segmentation
        .copy()
    )

    result[name_original_index] = pandas.RangeIndex(len(result))

    

    return result

