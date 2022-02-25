from typing import Optional
import pandas

from .shs import shs



SEGMENT_ID_COLUMN_NAME = "seg.id"

def homogenous_segmentation (
        data:pandas.DataFrame,
        measure:tuple[str, str], 
        variables:list[str], 
        allowed_segment_length_range:Optional[tuple[float, float]] = None
    ):
    """
    Homogeneous segmentation function with continuous variables.
    Modifies the input dataframe and returns it with a column "seg.id"

    Coppied from the original python port at <https://github.com/thehappycheese/HS> which was in turn
    ported from an [R package - also called HS](https://cran.r-project.org/web/packages/HS/index.html).
    The author of the original R package is **Yongze Song**, and it is related to the following paper:

    > Song, Yongze, Peng Wu, Daniel Gilmore, and Qindong Li. "[A spatial heterogeneity-based segmentation model for analyzing road deterioration network data in multi-scale infrastructure systems.](https://ieeexplore.ieee.org/document/9123684)" IEEE Transactions on Intelligent Transportation Systems (2020).

    Args:
        data (DataFrame): Dataframe to be modified
        measure (tuple[str,str]): Names of column indicating start SLK (linear / spatial measure). eg ("slk_from", "slk_to")
        variables (list[str]): A list of column names reffering to the continuous numeric variables to be used by the segmentation method. eg ["roughness","deflection"]
        
        allowed_segment_length_range (Optional[tuple[float,float]]):  Maximum and minimum segment lengths.
            Note that rows will not be split if they are already larger than the minimum. 
            If nothing is provided then the min length of existing segments will be used as minimum
            and the sum of all segment lengths will be used as the maximum.
            This function only groups rows by adding the index column "seg.id"

    Returns:
        The original dataframe with new columns `'seg.id'` and `'seg.point'`.
        `'seg.id'` is an integer, and `'seg.point'` is zero everywhere except for the start of a new segment.

    """

    measure_start, measure_end = measure

    # preprocessing
    data = (
        data
        .dropna(subset=variables)
        .sort_values(by=measure_start)
        .reset_index(drop=True)
    )

    # add length # remove system errors of small data
    data["length"] = (data[measure_end] - data[measure_start]).round(decimals=10)

    if allowed_segment_length_range is None:
        allowed_segment_length_range = (
            data["length"].min(),
            data["length"].sum()
        )

    if data["length"].sum() <= allowed_segment_length_range[1]:
        data[SEGMENT_ID_COLUMN_NAME] = 1
    else:	
        data = shs(data, var = variables, length = "length", allowed_segment_length_range = allowed_segment_length_range)

    return data
