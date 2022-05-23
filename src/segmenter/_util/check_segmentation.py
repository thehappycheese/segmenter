def check_monotonically_increasing_segments(df, categories:list[str], measure:tuple[str,str]):
    """
    Check that the segments are monotonically increasing;
    Every segment in each category must start at or after the end of the previous segment

    - Note: does not perform a sort. Input data must be pre-sorted by measure[0]
    """
    return all(
        (values[measure[0]] >= values[measure[1]].shift(1, fill_value=0)).all()
        for _index, values
        in df.groupby(categories)
    )

def check_no_reversed_segments(df, measure:tuple[str,str]):
    """
    Check that the measure[0] <= measure[1] for every segment
    """
    return (df[measure[0]]<=df[measure[1]]).all()
    