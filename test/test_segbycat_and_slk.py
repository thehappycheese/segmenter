import pandas as pd
import numpy as np
from segmenter._util.by_category import segment_by_categories_and_slk_discontinuities




def test_segbycat_and_slk():

     #data[CATEGORY_COLUMN_NAME] = data.groupby(by_category).ngroup() + 1

    data_to_segment = pd.read_csv("./test/test_data/df2.csv")
    data_to_segment["original_sort_order"] = data_to_segment.index

    data_to_segment["seg.ctg"] = segment_by_categories_and_slk_discontinuities(
        data=data_to_segment,
        categories=["road","cwy","dirn"],
        measure_slk=("slk_from","slk_to")
    )

    # pretty sure the above function is fine based on manual testing, 
    # but so that we can compare it with the old R output we 
    # have to re-sort it and renumber seg.ctg
    # df = df.sort_values(by=["road","cwy","dirn", "slk_from"])

    # SEG_CTG_SLK_START = "seg.ctg-slk_start"

    # df = (
    #     df
    #     .join(
    #         (
    #             df
    #             .groupby(["seg.ctg"])
    #             .agg({"slk_from":"min"})
    #             .rename(columns={"slk_from":SEG_CTG_SLK_START})
    #         ),
    #         on=["seg.ctg"]
    #     )
    #     .sort_values(by=["road", "dirn", SEG_CTG_SLK_START, "cwy"])
    #     .drop(columns=SEG_CTG_SLK_START)
    #     .reset_index(drop=True)
    # )
    # ctg_remap     = df["seg.ctg"].unique()
    # ctg_remap     = pd.Series(np.arange(len(ctg_remap)), index = ctg_remap)
    # df["seg.ctg"] = df["seg.ctg"].map(ctg_remap) + 1

    data_to_segment = data_to_segment.sort_values(by="original_sort_order")

    r_output = pd.read_csv("./test/r_outputs/df2_segcat_out.csv")
    # assert r_output.compare(df).empty

    # the above test method does not work because there are additional spatial breaks due to SLK discontinuities
    # the best we can do is check that whereever the R output breaks, the new method breaks also
    df_changes = (data_to_segment["seg.ctg"].values[:-1] != data_to_segment["seg.ctg"].values[1:])
    r_changes  =  (r_output["seg.ctg"].values[:-1] != r_output["seg.ctg"].values[1:])

    assert np.all(r_changes == np.logical_and(df_changes, r_changes))


    