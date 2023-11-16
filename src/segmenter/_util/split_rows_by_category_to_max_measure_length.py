from typing import List, Tuple
import pandas
import numpy as np
from .by_category import segment_by_categories_and_slk_true_discontinuities
from .linspace_steps import linspace_steps

def split_rows_by_category_to_max_segment_length(
    data:pandas.DataFrame,
    measure_slk:Tuple[str,str],
    measure_true:Tuple[str,str],
    categories:List[str],
    max_segment_length:float,
    min_segment_length:float=0,
) -> pandas.DataFrame:
    """
    Split rows by category, then into segments of even length.
    The SLK of each segment will be at integer multiples of `max_segment_length`.

    Other columns of the dataframe are ignored.
    
    Each `segment_index` in the output will have only one distinct value for the columns `original_index_from` and `original_index_to`.

    Args:
        data (pandas.DataFrame):              data to be segmented
        measure_slk (tuple[str,str]):         column names of slk measure to segment by; eg ("slk_from", "slk_to")
        measure_true (tuple[str,str]):        column names of true measure to segment by; eg ("true_from", "true_to")
        categories (list[str]):               column names of categories to segment by; eg ["road", "cwy"]
        max_segment_length (float):           This is the target segment length. May not be achieved at the segment ends. Segments will be made at integer multiples of this value.
        min_segment_length (float, optional): Segments shorter than this will be merged with adjacent segments. Only happens to the first and last observation in each segment id. Default is Zero.
    Returns:
        pandas.DataFrame: 
    """

    # check none of the slk columns are the same as true columns
    if set(measure_slk) & set(measure_true):
        raise ValueError(
            f"The columns selected in parameter `measure_slk` must all be different to those in `measure_true`; "
            f"Found {set(measure_slk) & set(measure_true)} in common."
            f" If you do not have true distance columns then you should duplicate the slk columns with new names before calling this function.")

    
    # segment_index is like the "network_element" field in the imaginary geometry table
    segment_index    = segment_by_categories_and_slk_true_discontinuities(
        data         = data,
        measure_slk  = measure_slk,
        measure_true = measure_true,
        categories   = categories
    )

    # This copy would not be necessary, except the user may pass in a heavily filtered view
    # then, when we try assign stuff to this frame we will get errors.
    data = data.copy()

    data["__segment_index"] = segment_index

    data["__original_order"] = np.arange(len(data)).astype(np.int64)
    data = data.sort_values(by=[*categories, "__segment_index"])
    data["__sorted_order"  ] = np.arange(len(data)).astype(np.int64)

    # the following table is an intermediate result;
    # each row represents a single "segment" of the network, as determined by the behaviour of the 
    # segment_by_categories_and_slk_true_discontinuities function. Please see that function's docstring for more details.
    # each row in the following table will be expanded into a continuous chunk of evenly spaced observations in the output table.
    new_index_summary = (
        data
        .groupby([*categories, "__segment_index"])
        .aggregate({
            measure_slk[0]: "min",
            measure_slk[1]: "max",
            measure_true[0]: "min",
            measure_true[1]: "max",
            "__sorted_order": ["min","max"],
        })
    )

    # create lists to hold the new data in chunks
    sub_results_slk_true = []
    sub_results_min_max_original_index = []
    sub_results_indexes = [[] for _ in range(len(categories)+1)]

    # stretch index;
    MOD_result_index = new_index_summary.index.repeat(
        new_index_summary.loc[:,("__sorted_order","max")] - new_index_summary.loc[:,("__sorted_order","min")]
    )


    # The following logic is similar to a pandas.DataFrame.reindex() call with an Index.repeat()
    for (
            index,
            slk_from,
            slk_to,
            true_from,
            true_to,
            sorted_index_from,
            sorted_index_to
        ) in new_index_summary.itertuples(index=True):

        if(slk_to-slk_from == true_to-true_from):
            # if the slk spacing is the same as true spacing we can make the SLK's land on nice round multiples of the spacing
            new_slks = linspace_steps(
                measure_from   = slk_from,
                measure_to     = slk_to,
                multiples      = max_segment_length,
                minimum_length = min_segment_length
            )

            new_trues = np.round(
                (new_slks - slk_from)
                / (slk_to   - slk_from)
                * (true_to  - true_from)
                +  true_from,
                3
            )
        else:
            new_trues = linspace_steps(
                measure_from   = true_from,
                measure_to     = true_to,
                multiples      = max_segment_length,
                minimum_length = min_segment_length
            )

            new_slks = np.round(
                (new_trues - true_from)
                / (true_to  - true_from)
                * (slk_to   - slk_from)
                +  slk_from,
                3
            )

        sub_results_slk_true.append(
            np.array([
                    new_slks [ :-1],
                    new_slks [1:  ],
                    new_trues[ :-1],
                    new_trues[1:  ],
                ])
        )

        # collect these original index columns separately
        # so that when they are added to the dataframe they don't
        # get converted to floats
        # max rows allowed by u4; 4,294,967,295
        sub_results_min_max_original_index.append(
            np.array([
                np.full(len(new_slks)-1, sorted_index_from, dtype= "u4"),
                np.full(len(new_slks)-1, sorted_index_to,   dtype= "u4"),
            ])
        )

        # we have to collect each level of the index separately
        # otherwise numpy will coerce them all to a single type, normally a string.
        for sub_index, sub_results_index in zip(index, sub_results_indexes):
            sub_results_index.append(
                np.repeat(sub_index, len(new_slks)-1)
            )

    # stack up the columns collected in the for-loop
    sub_results_indexes = [
        np.concatenate(sub_results_index) for sub_results_index in sub_results_indexes
    ]
    
    sub_results_slk_true = np.concatenate(sub_results_slk_true, axis=1)
    


    # build the result dataframe
    # contains index / columns that look like
    # (*categories, segment_index) / (slk_from, slk_to, true_from, true_to)
    result = pandas.DataFrame(
        sub_results_slk_true.transpose(),
        index=pandas.MultiIndex.from_arrays(
            arrays = sub_results_indexes,
            names  = [*categories, "segment_index"]
        ),
        columns    = [*measure_slk, *measure_true],
    )
    # afterwards add two more columns (cant be built into the call above otherwise dtypes will be forced to match sub_results_slk_true)
    result["__sorted_index_from"], result["__sorted_index_to"  ] = np.concatenate(
        sub_results_min_max_original_index,
        axis=1
    )
    

    # NOTE: `segment_index` created above is like the "network_element" field in the imaginary geometry table.
    #        Perhaps it should be renamed "chunk index" or "group index" or "segment_grouping_id"?
    
    # recombine the result (which is now basically just a giant MultiIndex)
    # with original data columns that got left behind
    
    # TODO: warning; will fail if data has complex index?
    recombination_index = _recombine_segmentation_index(
        segmentation   = result,
        original_data  = data,
        measure        = measure_true,
        grouping_id    = "segment_index",
        grouping_range = ("__sorted_index_from", "__sorted_index_to")
    )
    
    # get a list of column names that are not part of the index we built
    value_columns = list(set(data.columns) - {*categories, *measure_slk, *measure_true})

    result = (
        result
        .join(
            data[value_columns],
            how="left",
            on=recombination_index
        )
        .drop(columns=[
            "__sorted_index_from",
            "__sorted_index_to",
            "__sorted_order",
            "__original_order",
            "__segment_index"
        ])
    )

    return result



def _recombine_segmentation_index(
        segmentation:pandas.DataFrame,
        original_data:pandas.DataFrame,
        measure:Tuple[str,str],
        grouping_id:str,
        grouping_range:Tuple[str,str],
    ) -> pandas.Series:
    """
    For each observation in `segmentation` finds the matching
    integer index in the `original_data` based on the columns
    named measure[0] and measure[1]. The longest overlapping
    segment will be returned, regardless of whether the values
    in `original_data` are missing.

    Args:
        segmentation (pandas.DataFrame):
        original_data (pandas.DataFrame):
        measure (tuple[str,str]): Typically used with ("true_from", "true_to")
        grouping_id (str): Column name that groups observation in `segmentation` into continuous chunks.
            Each chunk corresponds to an unbroken linestring element in the imaginary geometry table.
        grouping_range (tuple[str,str]): The name of the two columns in the `segmentation` which identify
            the start index and end index of the `original_data` which the observation in `segmentation`
            may overlap. Typically `("__sorted_index_from", "__sorted_index_to")`.
    Returns:
        pandas.Series: The row label / index of the observation in `original_data`
                       that matches the observation in `segmentation`.
    """

    

    # segment_index is like the "network_element" field in the imaginary geometry table
    # it is defined in the function above and is subject to change.
    result = []
    result_index = []
    for _index, group in segmentation.groupby(grouping_id):
        original_data_possibly_overlapping = (
            original_data
            .iloc[
                group.loc[:,grouping_range[0]].iloc[0]:group.loc[:, grouping_range[1]].iloc[0]+1
            ]
            [list(measure)]
        )

        # pandas uses named tuples which is super annoying to work with
        # here we get the index of the fields we want in advance.
        # we add 1 because itertuples inserts the index as item zero
        measure_from_index = group.columns.get_loc(measure[0]) + 1
        measure_to_index   = group.columns.get_loc(measure[1]) + 1

        for itertup in group.itertuples(index=True):
            index = itertup[0]
            group_measure_from = itertup[measure_from_index]
            group_measure_to   = itertup[  measure_to_index]

            #                                                                Series,       Scalar Float
            overlap_min = np.maximum(original_data_possibly_overlapping[measure[0]], group_measure_from)
            overlap_max = np.minimum(original_data_possibly_overlapping[measure[1]],   group_measure_to)
            
            # overlap_len = np.maximum(overlap_max - overlap_min, 0)  # np.maximum() is not needed due to filters above
            overlap_len = overlap_max - overlap_min

            mask_overlaps_greater_than_zero = overlap_len > 0

            if not np.any(mask_overlaps_greater_than_zero):
                # Infill with np.nan or we will lose our column position.
                result.append(np.nan)
                result_index.append(index)
                continue
            
            # Here we are merging whichever observation has the longest overlap
            # we are unable to find the "longest non-null overlap" since we are looking at multiple columns
            # in the merge tool we work with one column at a time, and therefore we can decide which observation to choose

            # this next line would be the beginning of an implementation that would allow us to choose the "longest non-null overlap"
            # but for the moment this attempt is abandoned.
            # original_data_actually_overlapping = original_data_possibly_overlapping.loc[mask_overlaps_greater_than_zero]
            
            result_index.append(index)

            result.append(
               overlap_len[mask_overlaps_greater_than_zero].idxmax()
            )
    
    return pandas.Series(result, index=result_index)
