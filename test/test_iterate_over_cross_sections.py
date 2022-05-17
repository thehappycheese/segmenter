

def test_cross_sections():
    import pandas as pd
    from segmenter import cross_sections

    data_to_iterate_over = pd.DataFrame(
        columns=["road_no", "carriageway", "xsp", "slk_from", "slk_to", "true_from", "true_to", "value"],
        data=[
            ["H001", "L", "L1", 0.010, 0.050, 0.010, 0.050, "a"], # SLK discontinuity (gap)
            ["H001", "L", "L1", 0.050, 0.070, 0.050, 0.070, "b"],
            ["H001", "L", "L1", 0.080, 0.100, 0.070, 0.090, "c"],
            ["H001", "L", "L1", 0.100, 0.120, 0.090, 0.110, "d"],

            ["H001", "L", "L2", 0.010, 0.050, 0.010, 0.050, "a"], # TRUE discontinuity (gap, overlaps not permitted for true)
            ["H001", "L", "L2", 0.050, 0.070, 0.050, 0.070, "b"],
            ["H001", "L", "L2", 0.070, 0.080, 0.070, 0.080, "c"],
            ["H001", "L", "L2", 0.080, 0.090, 0.090, 0.110, "d"],
            ["H001", "L", "L2", 0.090, 0.100, 0.110, 0.120, "e"],

            ["H001", "L", "L3", 0.080, 0.100, 0.070, 0.090, "e"], # XSP discontinuity
            ["H001", "L", "L3", 0.100, 0.120, 0.090, 0.110, "f"],

            ["H001", "R", "L3", 0.010, 0.050, 0.010, 0.050, "a"], # SLK discontinuity (overlap)
            ["H001", "R", "L3", 0.050, 0.070, 0.050, 0.070, "b"],
            ["H001", "R", "L3", 0.050, 0.060, 0.070, 0.080, "c"],
            ["H001", "R", "L3", 0.060, 0.070, 0.080, 0.100, "d"],
            ["H001", "R", "L3", 0.070, 0.090, 0.100, 0.110, "e"],

            ["H002", "L", "L1", 0.010, 0.050, 0.010, 0.050, "a2"],
            ["H002", "L", "L2", 0.010, 0.050, 0.010, 0.050, "a2"],
            ["H002", "L", "L1", 0.050, 0.090, 0.050, 0.090, "a2"],
            ["H002", "L", "L1", 0.090, 0.150, 0.090, 0.150, "a2"],
            ["H002", "L", "L2", 0.090, 0.150, 0.090, 0.150, "a2"],

        ]
    )

    kk = cross_sections(
        data_to_iterate_over,
        ["road_no"],
        ["carriageway", "xsp"],
        ("slk_from", "slk_to"),
        ("true_from", "true_to"),
    )


    raise Exception("Test not written yet")