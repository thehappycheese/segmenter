

import pytest


def test_check_linear_index():
    import pandas as pd
    import numpy as np
    from segmenter._util.check_segmentation import check_linear_index

    # passiing test
    df = pd.DataFrame(
        columns=["slk_from", "slk_to"],
        data=[
            [0,1],
            [1,2],
        ],
    )
    check_linear_index(df, must_be_ordered_and_disjoint=True)


    with pytest.raises(ValueError, match="exactly two"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to","slk"],
            data=[
                [0,1,0],
                [1,2,0],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    
    with pytest.raises(TypeError, match="not a numeric"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                ["0",1.0],
                ["1",2.0],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)

    with pytest.raises(TypeError, match="not a numeric"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,"1.0"],
                [1,2.0],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    
    with pytest.raises(ValueError, match="NaN"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,1],
                [1,np.nan],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)

    with pytest.raises(ValueError, match="first column is greater"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,1],
                [3,1],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)

    with pytest.raises(ValueError, match="zero length"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,1],
                [3,3],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    
    # the following three are ok only if must_be_ordered_and_disjoint=False

    with pytest.raises(ValueError, match="monotonic increasing"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [1,2],
                [0,3],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    check_linear_index(df, must_be_ordered_and_disjoint=False)
    
    with pytest.raises(ValueError, match="monotonic increasing"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,2],
                [1,1.5],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    check_linear_index(df, must_be_ordered_and_disjoint=False)
    
    with pytest.raises(ValueError, match="not disjoint"):
        df = pd.DataFrame(
            columns=["slk_from", "slk_to"],
            data=[
                [0,2],
                [1,3],
            ],
        )
        check_linear_index(df, must_be_ordered_and_disjoint=True)
    check_linear_index(df, must_be_ordered_and_disjoint=False)