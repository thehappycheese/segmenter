


from typing import Optional
import pandas
import numpy as np
CATEGORY_COLUMN_NAME = "seg.ctg"



def segment_by_categories_and_slk_discontinuities(
        data:pandas.DataFrame,
        categories:list[str],
        measure_slk:tuple[str,str],
    ):
    """
    Returns a series containing integer segment labels:
    A new 'segment' is started whenever one of the `categories` changes or
    any time there is a discontinuity in the slk measure.
    
    
    Please Note:
    
    - For each unique combination of `categories` in the input `data`, the range `slk_from` to `slk_to` for observations **must** be non-overlapping.
    - No check is made for overlapping observations in this function, it is actually very computationally intensive to do so. I might write a utility that does it one day.
    - Weird stuff will happen if there are overlaps
    - You have been warned

    Internally, data is sorted by the `categories` (in order provided) then by 
    `measure_slk[0]` prior to seeking discontinuities then labeling.

    Args:
        data (pandas.DataFrame):       data to be segmented
        categories (list[str]):        column names of categories to segment by; eg ["road", "cwy"] or ["road", "cwy", "xsp"]
        measure_slk (tuple[str,str]):  column names of slk measure to segment by; eg ("slk_from", "slk_to")
    Returns:
        pandas.Series: A series of integers which label the segment_id of each row.
        A series with an index that is compatible
        with the input `data` such that it can be easily joined or assigned to the original dataframe.
        See example below for suggested usage.
        

    Example:
    
    ```python
    df["segment_id"] = segment_by_categories_and_slk_true_discontinuities(
        data         = df,
        categories   = ["road", "cwy", "xsp"],
        measure_slk  = ("slk_from", "slk_to"),
        measure_true = ("true_from", "true_to")
    )
    ```
    """
    
    # We cheat here by calling into the other function
    # this is a neat hack that will make testing and maintaining easier at the tiny cost of repeated work
    # TODO: actually test if this is working as expected
    return segment_by_categories_and_slk_true_discontinuities(
        data,
        categories,
        measure_slk,
        measure_slk 
    )

def segment_by_categories_and_slk_true_discontinuities(
        data:pandas.DataFrame,
        categories:list[str],
        measure_slk:tuple[str,str],
        measure_true:tuple[str,str]
    ) -> pandas.Series:
    """
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

    Args:
        data (pandas.DataFrame):       data to be segmented
        categories (list[str]):        column names of categories to segment by; eg ["road", "cwy"] or ["road", "cwy", "xsp"]
        measure_slk (tuple[str,str]):  column names of slk measure to segment by; eg ("slk_from", "slk_to")
        measure_true (tuple[str,str]): column names of true measure to segment by; eg ("true_from", "true_to")
    Returns:
        pandas.Series: A series of integers which label the segment_id of each row.
        A series with an index that is compatible
        with the input `data` such that it can be easily joined or assigned to the original dataframe.
        See example below for suggested usage.
        

    Example:
    
    ```python
    df["segment_id"] = segment_by_categories_and_slk_true_discontinuities(
        data         = df,
        categories   = ["road", "cwy", "xsp"],
        measure_slk  = ("slk_from", "slk_to"),
        measure_true = ("true_from", "true_to")
    )
    ```

    """
    
    measure_slk_from, measure_slk_to = measure_slk
    measure_true_from, measure_true_to = measure_true
    
    # note: after this line, we must not touch the index of this dataframe until it is recombined with the result at the end of this function
    data = data.sort_values(by=[*categories, measure_true_from])

    result_column = data.set_index(categories).loc[:,[]]
    
    

    offset = 0
    for group_index, group in data.groupby(categories):

        slk_discontinuities = (   
           np.around(group[  measure_slk_to].values[ :-1], 3)
        != np.around(group[measure_slk_from].values[1:  ], 3)
        )
        
        true_discontinuities = (
            np.around(group[  measure_true_to].values[ :-1], 3)
            != np.around(group[measure_true_from].values[1:  ], 3)
        )

        # discontinuities is a boolean array, true at each index where a discontinuity occurs
        discontinuities = slk_discontinuities | true_discontinuities

        # but taking the cumulative sum of this array will give us the index of the first observation in each segment
        cat_values = np.cumsum(
            np.append(
                np.full(1,False),
                discontinuities
            )
        )

        result_column.loc[group_index, "seg.ctg"] = cat_values + offset
        offset += max(cat_values)+1
    

    # Note: the following strips the index from result_column 
    # and relies on sort order to join with original data.index
    return pandas.Series(
        result_column.iloc[:,0].values.astype("u4"),
        index=data.index
    )



def segment_by_cross_section(
        data,
        categories:list[str],
        lane_category:str,
        measure_slk:tuple[str,str],
        measure_true:tuple[str,str]
    ):
    """
    Returns a series containing integer segment labels:
    A new 'segment' is started whenever one of the `categories` changes or
    """
    data[segmentation_id]
