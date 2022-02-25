
import pandas as pd
import numpy as np

def test_split_rows_by_category_to_max_segment_length():
    
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
    
    #result = result.drop(columns="old_index")


    
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

    #expected_result["original_index_from"] = expected_result["original_index_from"].astype("u4")
    #expected_result["original_index_to"]   = expected_result["original_index_to"].astype("u4")
    
    # np.concatenate(np.array([
    #     np.array([*map(list, result.index)]),
    #     np.array([*map(list, result.index)]),
    # ]), axis=1)
    #     np.transpose(np.expand_dims(result.index==expected_result.index, 0))

    pd.testing.assert_frame_equal(
        result,
        expected_result,
        check_like =False, # ignore column order and label order
    )