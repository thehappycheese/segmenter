from __future__ import annotations
import pandas as pd


from .Addable import Addable
from .ImmutableTree import ImmutableTree, ImmutableTreeMergeError
from .Transition import Transition

class CN:
    """Column Names"""
    event_measure_true  = "__event_measure_true__"
    event_measure_slk   = "__event_measure_slk__"
    event_type          = "__event_type__"
    event_effect        = "__event_effect__"
    event_effect_cumsum = "__event_effect_cumsum__"
    event_measure_diff  = "__event_measure_diff__"
    event_trees         = "__event_trees__"
    group_number        = "__group_number__"


def cross_sections(
    segmentation:pd.DataFrame,
    group_categories:list[str],
    cross_section_categories:list[str],
    measure_slk:tuple[str,str],
    measure_true:tuple[str,str],
    out_col_name_cross_section_number:str = "cross_section_number",
    out_col_name_original_index:str = "original_index",
    out_col_name_overlap_index:str = "overlap",
)->pd.DataFrame:

    """
    Please see documentation for `cross_sections_normalised()` for the time being
    """
    
    output_rows = []
    for group_counter, (group_index, group) in enumerate(segmentation.groupby(group_categories)):
        
        group = group[[*group_categories, *cross_section_categories, *measure_true, *measure_slk]]#.reset_index(drop=True)

        # capture segment start events, sort ascending
        start_events = group.copy().sort_values(by=cross_section_categories, ascending=True)
        start_events[CN.event_measure_true] = start_events[measure_true[0]]
        start_events[CN.event_measure_slk]  = start_events[measure_slk[0]]
        start_events[CN.event_type]         = "start"
        start_events[CN.event_effect]       = +1
        
        # capture segment end events, sort decending
        end_events = group.copy().sort_values(by=cross_section_categories, ascending=False)
        end_events[CN.event_measure_true] = end_events[measure_true[1]]
        end_events[CN.event_measure_slk]  = end_events[measure_slk[1]]
        end_events[CN.event_type]         = "end"
        end_events[CN.event_effect]       = -1

        # combine start and end events and sort using stable sort
        events:pd.DataFrame = pd.concat([end_events, start_events], axis='index')
        events = events.sort_values(by=CN.event_measure_true, kind="stable")
        # the cumulative sum of event_effect and the
        events[CN.event_effect_cumsum] = events[CN.event_effect].cumsum()

        # this next line changes the dtype
        #events["event_measure_diff"] = events["event_measure"].diff().fillna(0)
        # this next version avoids changing the dtype, but has a different value for the first row;
        # But It turns out this doesnt matter since we only look at this column [1:]
        #events[CN.event_measure_diff] = events[CN.event_measure_true] - events[CN.event_measure_true].shift(1, fill_value=0)
        events[CN.event_measure_diff] = events[CN.event_measure_true] - events[CN.event_measure_true].shift(1, fill_value=events[CN.event_measure_true].iloc[0])

        # use a special tree stack type to build up list of transitions
        # each transition occurs when the cross section changes
        past_trees = []
        current_tree = ImmutableTree()
        for index, row in events.iterrows():
            csc:list[str] = row[cross_section_categories]
            if row[CN.event_type]=="start":
                current_tree = current_tree.add_data(csc, Addable([(index, 1)]))
                past_trees.append(current_tree)
            elif row[CN.event_type]=="end":
                current_tree = current_tree.remove_data(csc, Addable([(index, 1)]))
                past_trees.append(current_tree)
        events[CN.event_trees] = [item for item in past_trees] # TODO: why list comprehension

        # pair down transitions such that we only capture non-zero length cross-sections
        transitions:list[Transition] = []
        #last_index = events.index[0]
        last_row = events.iloc[0]
        for _index, row in events.iloc[1:].iterrows():
            if row[CN.event_measure_diff] > 0:
                transitions.append(
                    Transition(
                        measure_true_from = last_row[CN.event_measure_true],
                        measure_true_to   = row[CN.event_measure_true],
                        measure_slk_from  = last_row[CN.event_measure_slk],
                        measure_slk_to    = row[CN.event_measure_slk],
                        tree              = last_row[CN.event_trees],
                    )
                )
                # NOTE: The selection of `measure_slk_from` and `measure_slk_to` above are  wrong, but impossible to fix;
                #       if we take a cross section over two carriageways (where the SLK system is different), then it is not possible to guarantee
                #       1) that we have selected a coherent SLK `from` and `to`. Maybe `from` > `to`?
                #       2) that points of equation are correctly handled.
                #       We can at least guarantee that the selected SLKs DO EXIST as we are not interpolating between SLKs.
            #last_index = index
            last_row = row
        
        mapped_transitions:list[Transition] = [
            transition.map_tree(lambda item: (item[0], transition.measure_true_to - transition.measure_true_from))
            for transition
            in transitions
        ]

        merged_transitions:list[Transition] = []
        transition_accumulator = mapped_transitions[0]
        for transition in mapped_transitions[1:]:
            #measure_from,      measure_to,      tree      = transition
            #measure_from_last, measure_to_last, tree_last = transition_accumulator
            try:
                transition_accumulator = transition_accumulator.accumulate(transition)
            except ImmutableTreeMergeError:
                merged_transitions.append(transition_accumulator)
                transition_accumulator = transition
        # append the last transition
        merged_transitions.append(transition_accumulator)
        
        group_index_list = [group_index] if not isinstance(group_index, tuple) else group_index

        for cross_section_number, (transition) in enumerate(merged_transitions):
            for child_name, child_data in transition.tree.iter_leaf_data():
                for child_data_sub in child_data:
                    output_rows.append([
                        group_counter,
                        cross_section_number,
                        *group_index_list,
                        *child_name,
                        transition.measure_true_from,
                        transition.measure_true_to,
                        transition.measure_slk_from,
                        transition.measure_slk_to,
                        *child_data_sub
                    ])
    
    result = pd.DataFrame(
        data=output_rows,
        columns=[
            CN.group_number,
            out_col_name_cross_section_number,
            *group_categories,
            *cross_section_categories,
            *measure_true,
            *measure_slk,
            out_col_name_original_index,
            out_col_name_overlap_index
        ]
    )

    result.loc[:,out_col_name_cross_section_number] = (
        result.loc[:,out_col_name_cross_section_number]
        +
        result[[CN.group_number]].join(
            (result.groupby(CN.group_number)[out_col_name_cross_section_number].max()+1).cumsum().shift(1, fill_value=0),
            on=CN.group_number
        ).loc[:,out_col_name_cross_section_number]
    )

    return result.drop(columns=[CN.group_number])


def cross_sections_normalised(
        segmentation:                      pd.DataFrame,
        group_categories:                  list[str],
        cross_section_categories:          list[str],
        measure_slk:                       tuple[str,str],
        measure_true:                      tuple[str,str],
        out_col_name_cross_section_number: str = "cross_section_number",
        out_col_name_original_index:       str = "original_index",
        out_col_name_overlap_index:        str = "overlap",
    ):
    """
    Takes a `segmentation` dataframe and returns a tuple of two dataframes 
    (`group_table`, `cross_section_table`).
    
    See also the `cross_sections()` function which performs the same task but returns a single dataframe.

    Segmentation is a self-overlapping dataset containing a categorical index, and a linear spatial index.
    
    For example, a road surface dataset may have

    - a categorical index `["ROAD_NUMBER"]`
    - a cross-sectional index `["CARRIAGEWAY", "LANE_NUMBER"]`
    - and a spatial index `["TRUE_CHAINAGE_FROM", "TRUE_CHAINAGE_TO"]`
    - (and an auxiliary spatial index `["SLK_CHAINAGE_FROM", "SLK_CHAINAGE_TO"]`)

    This algorithm would then return a "cross section" along each `"ROAD_NUMBER"` at
    each change of `"CARRIAGEWAY"` and `"LANE_NUMBER"`.

    ```text
    ┌──────────────────────────────────────────────────────────────────────────────────────┐
    │Road                                     ┌─────────────────────────────────────┐      │
    │                                         │Carriageway = Left                   │      │
    │                                         │                   ┌───────────────┐ │      │
    │                                         │                   │Lane=L3        │ │      │
    │ ┌─────────────────────────────────────┐ │                   └───────────────┘ │      │
    │ │Carriageway = Single                 │ │ ┌───────────────┐ ┌───────────────┐ │      │
    │ │                   ┌───────────────┐ │ │ │Lane=L2        │ │Lane=L2        │ │      │
    │ │                   │ Lane=L2       │ │ │ └───────────────┘ └───────────────┘ │      │
    │ │                   └───────────────┘ │ │ ┌───────────────┐ ┌───────────────┐ │      │
    │ │ ┌───────────────┐ ┌───────────────┐ │ │ │Lane=L1        │ │Lane=L1        │ │      │
    │ │ │Lane=L1        │ │Lane=L1        │ │ │ └───────────────┘ └───────────────┘ │      │
    │ │ └───────────────┘ └───────────────┘ │ └─────────────────────────────────────┘      │
    │ │ ┌───────────────┐ ┌───────────────┐ │ ┌─────────────────────────────────────┐      │
    │ │ │Lane=R1        │ │Lane=R1        │ │ │Carriageway = Right                  │      │
    │ │ └───────────────┘ └───────────────┘ │ │ ┌───────────────┐ ┌───────────────┐ │      │
    │ └─────────────────────────────────────┘ │ │Lane=R1        │ │Lane=R1        │ │      │
    │                                         │ └───────────────┘ └───────────────┘ │      │
    │                                         │ ┌───────────────┐ ┌───────────────┐ │      │
    │                                         │ │Lane=R2        │ │Lane=R2        │ │      │
    │                                         │ └───────────────┘ └───────────────┘ │      │
    │                                         └─────────────────────────────────────┘      │
    └──────────────────────────────────────────────────────────────────────────────────────┘

    Sectioning by ["Road"] and cross section by ["Carriageway", "Lane"] would result in Sections 0 to 3 below:

       ⮤ Section 0        ⮤ Section 1        ⮤ Section 2        ⮤ Section 3
         S:(L1,R1)           S:(L2,L1,R1)       L:(L1,L2)          L:(L1,L2,L3)
                                                R:(R1,R2)          R:(R1,R2)

    Sectioning by ["Road", "Carriageway"] and cross section by ["Lane"] would result Sections 0 to 5 below:
    
       ⮤ Section 0        ⮤ Section 1        ⮤ Section 2        ⮤ Section 3
         S:(L1,R1)           S:(L2,L1,R1)       L:(L1,L2)          L:(L1,L2,L3)

                                              ⮤ Section 4        ⮤ Section 5
                                                R:(R1,R2)          R:(R1,R2)
    ```

    ---

    For example given the dataframe `sd`

    ```text
        ROAD_NO  CWAY  XSP  SLK_FROM  SLK_TO  TRUE_FROM  TRUE_TO
    0         H001     L   L1      0.00    0.04       0.00     0.04
    1         H001     L   L2      0.00    0.04       0.00     0.04
    2         H001     L   L1      0.04    0.06       0.04     0.06
    3         H001     L   L2      0.04    0.06       0.04     0.06
    4         H001     L   L3      0.04    0.06       0.04     0.06
    ...        ...   ...  ...       ...     ...        ...      ...
    137643    H924     S   L1      6.80    7.80       6.80     7.80
    137644    H924     S   R1      6.80    7.80       6.80     7.80
    137645    H924     S    R      6.80    7.80       6.80     7.80
    ```

    The cross sections can be found like this:

    ```python
    group_table, cross_section_table = cross_sections_normalised(
        segmentation             = sd[sd["ROAD_NO"].isin({"H001","H002"})],
        group_categories         = ["ROAD_NO","CWAY"],
        cross_section_categories = ["XSP"],
        measure_slk              = ("SLK_FROM", "SLK_TO"),
        measure_true             = ("TRUE_FROM", "TRUE_TO"),
    )
    ```

    The resulting `group_table` contains the following columns:

    ```text
          cross_section_number ROAD_NO CWAY  TRUE_FROM  TRUE_TO  SLK_FROM  SLK_TO
    0                        0    H001    L       0.00     0.04      0.00    0.04
    2                        1    H001    L       0.04     0.06      0.04    0.06
    5                        2    H001    L       0.06     0.08      0.06    0.08
    9                        3    H001    L       0.08     0.19      0.08    0.19
    11                       4    H001    L       0.19     0.24      0.19    0.24
    ...                    ...     ...  ...        ...      ...       ...     ...
    9259                  1010    H002    R      55.84    55.92     55.84   55.92
    9263                  1011    H002    R      55.92    55.94     55.92   55.94
    9266                  1012    H002    R      55.94    55.99     55.94   55.99
    9270                  1013    H002    R      55.99    56.01     55.99   56.01
    9273                  1014    H002    R      56.01    56.04     56.01   56.04

    [983 rows x 7 columns]
    ```

    The resulting `cross_section_table` contains the following columns:

    ```text
          cross_section_number XSP  original_index  overlap
    0                        0  L1               0     0.04
    1                        0  L2               1     0.04
    2                        1  L1               2     0.02
    3                        1  L2               3     0.02
    4                        1  L3               4     0.02
    ...                    ...  ..             ...      ...
    9270                  1013   L            9278     0.02
    9271                  1013  R1            9279     0.02
    9272                  1013  R2            9280     0.02
    9273                  1014   L            9281     0.03
    9274                  1014  R1            9282     0.03
    
    [9275 rows x 4 columns]
    ```
    """



    result = cross_sections(
        segmentation                      = segmentation,
        group_categories                  = group_categories,
        cross_section_categories          = cross_section_categories,
        measure_slk                       = measure_slk,
        measure_true                      = measure_true,
        out_col_name_cross_section_number = out_col_name_cross_section_number,
        out_col_name_original_index       = out_col_name_original_index,
        out_col_name_overlap_index        = out_col_name_overlap_index
    )
    # group table (each cross section id appears once)
    group_table = result[[
        out_col_name_cross_section_number,
        *group_categories,
        *measure_true,
        *measure_slk
    ]].drop_duplicates()
    # cross section table; one row per lane per cross section id
    cross_section_table = result[[
        out_col_name_cross_section_number,
        *cross_section_categories,
        out_col_name_original_index,
        out_col_name_overlap_index
    ]]
    
    return group_table, cross_section_table