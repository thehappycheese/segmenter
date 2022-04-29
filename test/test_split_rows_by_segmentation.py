


def test_split_rows_by_segmentation_without_poes():
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
        expected_result.drop(columns=["slk_from", "slk_to"]),
        check_like=False, # ignore column order and label order
    )