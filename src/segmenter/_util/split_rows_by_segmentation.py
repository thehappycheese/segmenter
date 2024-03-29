from typing import List, Tuple
import pandas
import numpy as np

from .check_segmentation import check_linear_index, check_linear_index_is_ordered_and_disjoint

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
        categories:List[str],
        measure_slk:Tuple[str,str],
        measure_true:Tuple[str,str],
        name_original_index:str,
        name_additional_index:str,
        relax_slk_checks:bool=False
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
        relax_slk_checks:  Relax the ordered and disjoint checks on the addititional_segments dataframe SLK columns. Sometimes it is valid to have an SLK_END < SLK_START when the segment lies inside a point of equation. False by default untill further testing.
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

    # since we do not preserve the original indexes due to the problems explained below
    # for now, we will force the user to use a range-index
    if not (original_segmentation.index == pandas.RangeIndex(len(original_segmentation.index))).all():
        raise ValueError(f"`original_segmentation` index is not a RangeIndex (0,1,2,3,...). This will cause problems downstream due to the index not being preserved. This will be fixed in the future. Please use `original_segmentation.reset_index()`")
    if not (additional_segmentation.index == pandas.RangeIndex(len(additional_segmentation.index))).all():
        raise ValueError(f"`additional_segmentation` index is not a RangeIndex (0,1,2,3,...). This will cause problems downstream due to the index not being preserved. This will be fixed in the future. Please use `additional_segmentation.reset_index()`")

    # check that all columns required by the parameters are present
    _check_columns_present("categories",   original_segmentation, categories,   "original_segmentation")
    _check_columns_present("measure_slk",  original_segmentation, measure_slk,  "original_segmentation")
    _check_columns_present("measure_true", original_segmentation, measure_true, "original_segmentation")
    
    _check_columns_present("categories",   additional_segmentation, categories,   "additional_segmentation")
    _check_columns_present("measure_slk",  additional_segmentation, measure_slk,  "additional_segmentation")
    _check_columns_present("measure_true", additional_segmentation, measure_true, "additional_segmentation")

    check_linear_index(original_segmentation[list(measure_slk)])
    check_linear_index(original_segmentation[list(measure_true)])
    check_linear_index_is_ordered_and_disjoint(original_segmentation, measure_true, categories)

    if not relax_slk_checks:
        check_linear_index(additional_segmentation[list(measure_slk)])
    check_linear_index(additional_segmentation[list(measure_true)])
    check_linear_index_is_ordered_and_disjoint(additional_segmentation, measure_true, categories)
    

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

