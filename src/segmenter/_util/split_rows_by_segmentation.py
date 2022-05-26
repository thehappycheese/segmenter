import pandas
import numpy as np
from .check_segmentation import check_monotonically_increasing_segments, check_no_reversed_segments

def _check_columns_present(name, df, column_names, df_name):
    if not all(item in df.columns for item in column_names):
        raise ValueError(f"{name} {[column_name for column_name in column_names if column_name not in df.columns]} not in `{df_name}`. Did you mean to use `{df_name}.reset_index(drop=False)`?")


class CN:
    original_index     = "original_index"
    original_df_num    = "original_df_num"
    additional_index   = "additional_index"
    event_measure_true = "event_measure_true"
    event_measure_slk  = "event_measure_slk"
    event_type         = "event_type"

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
    Combines two segmentations, returning a new dataframe. The new segmentation will

    - Have a split wherever either of the original dataframes had a split
    - Cover any area that is covered by either of the original dataframes

    NOTE 1: Self-intersecting inputs will produce invalid results!

    NOTE 2: Original indexes are not preserved!!!! the `original_index` and
    `additional_index` returned by this function are integer indexes which can be
    used with `.iloc[]` (not `.loc[]`) to retrieved rows from the original
    dataframes. This limitation may be removed in the future.

    Args:
        original_segmentation: A non-overlapping (in `measure_true`) segmentation over `categories`
        additional_segmentation: used to split `original_segmentation`
        categories: Typically `['road','carriageway']`
        measure_slk: Typically `('slk_from','slk_to')`
        measure_true: Typically `('true_from','true_to')`
        name_original_index: The desired name of the column that will be output into result. The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'original_index'`
        name_additional_index:  The desired name of the column that will be output into result. The value in this column will be the integer index of the row in `original_segmentation` that corresponds to each row of the `result`. Typically `'additional_index'`
    """
    
    if (name_original_index==name_additional_index):
        raise ValueError(f"`name_original_index` and `name_additional_index` cannot be the same: {name_original_index}")
    
    # force the user to drop any multi-index
    if isinstance(original_segmentation.index, pandas.MultiIndex):
        raise ValueError(f"`original_segmentation` has a MultiIndex which is not supported. Please use `original_segmentation.reset_index()`")
    if isinstance(additional_segmentation.index, pandas.MultiIndex):
        raise ValueError(f"`additional_segmentation` has a MultiIndex which is not supported. Please use `additional_segmentation.reset_index()`")

    # confirm indexes do not have duplicates
    if original_segmentation.index.has_duplicates:
        raise ValueError(f"`original_segmentation` has duplicates in its index. Please use `original_segmentation.reset_index()`")
    if additional_segmentation.index.has_duplicates:
        raise ValueError(f"`additional_segmentation` has duplicates in its index. Please use `additional_segmentation.reset_index()`")

    # check that all columns required by the parameters are present
    _check_columns_present("categories",   original_segmentation, categories,   "original_segmentation")
    _check_columns_present("measure_slk",  original_segmentation, measure_slk,  "original_segmentation")
    _check_columns_present("measure_true", original_segmentation, measure_true, "original_segmentation")
    
    _check_columns_present("categories",   additional_segmentation, categories,   "additional_segmentation")
    _check_columns_present("measure_slk",  additional_segmentation, measure_slk,  "additional_segmentation")
    _check_columns_present("measure_true", additional_segmentation, measure_true, "additional_segmentation")

    if not check_no_reversed_segments(original_segmentation, measure_true):
        raise ValueError(f"`original_segmentation` has reversed segments ({measure_true[0]}>{measure_true[1]}).")

    if not check_no_reversed_segments(additional_segmentation, measure_true):
        raise ValueError(f"`additional_segmentation` has reversed segments ({measure_true[0]}>{measure_true[1]}).")

    # TODO: there are problems with these next lines;
    #       the original indexes are dropped by the .loc[]
    #       and are replaced by a rangeindex.
    #       this is super safe, but kinda annoying and unexpected.

    oseg = (
        original_segmentation
        #.reset_index(drop=False) # will be lost due to loc[] anyway
        .loc[:,[*categories, *measure_slk, *measure_true]]
        .assign(**{
            CN.original_index: lambda df: pandas.RangeIndex(len(df.index)),
            CN.original_df_num:0
        })
        .copy()
    )
    

    aseg = (
        additional_segmentation
        #.reset_index(drop=False) # will be lost due to loc[] anyway
        .loc[:,[*categories, *measure_slk, *measure_true]]
        .assign(**{
            CN.original_index: lambda df: pandas.RangeIndex(len(df.index)),
            CN.original_df_num:1
        })
        .copy()
    )

    # TODO: these checks are expensive, are they strictly needed?
    # furthermore; if only SLK is available, then this check will likely fail if either dataframe includes a POE.
    # it seems that
    if not check_monotonically_increasing_segments(oseg, categories, measure_true):
        raise Exception("`original_segmentation` is not monotonically increasing over `categories` and `measure_true`. Either the `original_segmentation` is self-overlapping, or it is not sorted.  Please `.sort_values([*categories, *measure_true])` before calling this function.")
    if not check_monotonically_increasing_segments(aseg, categories, measure_true):
        raise Exception("`additional_segmentation` is not monotonically increasing over `categories` and `measure_true`. Either the `additional_segmentation` is self-overlapping, or it is not sorted. Please `.sort_values([*categories, *measure_true])` before calling this function.")


    from_events = pandas.concat([oseg, aseg])
    from_events[CN.event_measure_true] = from_events[measure_true[0]]
    from_events[CN.event_measure_slk] = from_events[measure_slk[0]]
    from_events = from_events.sort_values([CN.event_measure_true, CN.original_df_num], ascending=[True, True], kind="stable")
    from_events[CN.event_type] = "from"

    to_events = pandas.concat([oseg, aseg])
    to_events[CN.event_measure_true] = to_events[measure_true[1]]
    to_events[CN.event_measure_slk] = to_events[measure_slk[1]]
    to_events = to_events.sort_values([CN.event_measure_true, CN.original_df_num], ascending=[True, False], kind="stable")
    to_events[CN.event_type] = "to"

    events = pandas.concat([from_events, to_events]).sort_values([*categories, CN.event_measure_true, CN.original_index], kind="stable")#.sort_values([*categories,"event_measure"], kind="stable")

    results = []
    for group_index, group in events.groupby(categories):
        segments = []
        index_o = None
        index_a = None
        last_measure_true = None
        last_measure_slk = None
        for row_index, row in group.iterrows():
            if (
                not last_measure_true is None 
                and row[CN.event_measure_true] - last_measure_true > 0 
                and row[CN.event_measure_slk] - last_measure_slk > 0 
                and not(index_o is None and index_a is None)
                ):
                # We have found a Non-Zero length segment, append it to the record
                group_index_columns = [group_index] if isinstance(group_index, str) else group_index
                #               [*categories,            measure_slk[0],     measure_slk[1],              measure_true[0],     measure_true[1],              name_original_index,   name_additional_index]
                segments.append([*group_index_columns,   last_measure_slk,   row[CN.event_measure_slk],   last_measure_true,   row[CN.event_measure_true],   index_o,               index_a              ])
            if row[CN.event_type] == "from":
                # Toggle the index_o and index_a ON (storing the event start index)
                if row[CN.original_df_num] == 0:
                    index_o = row[CN.original_index]
                else:
                    index_a = row[CN.original_index]
            elif row[CN.event_type] == "to":
                # Toggle the index_o and index_a OFF (by setting to None)
                if row[CN.original_df_num] == 0:
                    index_o = None
                else:
                    index_a = None
            last_measure_true = row[CN.event_measure_true]
            last_measure_slk = row[CN.event_measure_slk]
        results += segments
    # TODO: sometimes `name_original_index` and `name_additional_index` are floating point and sometimes int depending if all rows have a value.
    
    column_names = [*categories,*measure_slk, *measure_true, name_original_index, name_additional_index]
    # this error should never happen now due to the index checks added above.
    # if len(results)>0 and len(column_names)!=len(results[0]):
    #     raise Exception(
    #          "split_rows_by_segmentation() has become confused about the number of columns\n"
    #         f"column_names: {column_names}\n"
    #         f"results[0]: {results[0]}"
    #     )
    result =  pandas.DataFrame(
        data=results,
        columns=column_names,
    ) 
    result[name_original_index]   = result[name_original_index  ].astype("f8")
    result[name_additional_index] = result[name_additional_index].astype("f8")
    return result

