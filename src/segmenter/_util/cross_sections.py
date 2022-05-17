from __future__ import annotations
from typing import Callable, Collection, Generator, Iterable, Iterator, Literal, Optional, Hashable, Any, Sequence
import pandas as pd
import itertools



class Addable:
    """A list of tuples that can be added to another list of tuples
    Each tuple contains a `(hashable_index, float_value)`.
    When the lists are added, they merge elements with the same index, either adding or subtracting from the float value.
    If the float component an element becomes zero then it is removed from the list.
    This is a dumpsterfire of overengineering, but arose from iterating on the algorithm.
    It is intended to refactored for a simpler datastructure."""
    __slots__ = ['_data']
    _data:list[tuple[Hashable, float]]

    def __init__(self, data:list[tuple[Hashable, float]]):
        self._data = data
    
    def __add__(self, other:Addable) -> Addable:
        new_data = sorted(self._data + other._data)
        return Addable([
            (groupby_index, the_sum)
            for groupby_index, index_overlap_iterator in
            itertools.groupby(new_data, lambda item:item[0])
            if abs(the_sum:=sum(item[1] for item in index_overlap_iterator)) > 1e-6
        ])

    def __neg__(self) -> Addable:
        return Addable([(item[0], -item[1]) for item in self._data])
    
    def __sub__(self, other:Addable) -> Addable:
        return self + (-other)
    
    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        inner = ', '.join(f'({item[0]}, {item[1]:.3f})' for item in self._data)
        return f"[{inner}]"

    def copy(self) -> Addable:
        return Addable(self._data.copy())
    
    def map(self, func:Callable[[tuple[Hashable, float]], tuple[Hashable, float]]) -> Addable:
        return Addable([func(item) for item in self._data])

    def __iter__(self) -> Iterator[tuple[Hashable, float]]:
        return iter(self._data)



class ImmutableTreeMergeError(Exception):
    pass

class ImmutableTree:
    """
    This is not a very clever implementation of a Tree storage structure.
    It was cobbled together while itterating on the algorithm.
    It is intended to be replaced with a refactored version.
    """
    __slots__ = (
        #'_parent',
        '_children',
        '_data',
    )

    #_parent:Optional[ImmutableTree]
    _children:dict[str, ImmutableTree]
    _data:Addable
    

    def __init__(self):#, parent:Optional[ImmutableTree], children:Optional[dict[str,ImmutableTree]]=None, data:Optional[Addable]=None):
        #self._parent   = parent
        self._children = {} if children is None else children
        self._data     = Addable([]) if data is None else data
    
    # def root(self) -> ImmutableTree:
    #     if self._parent is None:
    #         return self
    #     return self._parent.root()

    def is_leaf(self) -> bool:
        return len(self._children) == 0
    
    def is_empty_leaf(self) -> bool:
        return len(self._children) == 0 and len(self._data) == 0

    def deep_clone(self, new_parent:Optional[ImmutableTree]) -> ImmutableTree:
        clone = ImmutableTree(new_parent)
        clone._data = self._data.copy()
        for key, value in self._children.items():
            clone._children[key] = value.deep_clone(clone)
        return clone

    def prune(self) -> Optional[ImmutableTree]:
        if len(self._children) == 0 and len(self._data) == 0:
            return None
        else:
            result = self.deep_clone(self._parent)
            result._children = {
                child_name:child_pruned 
                for child_name, child in result._children.items() 
                if (child_pruned:=child.prune()) is not None
            }
            return result

    def add_data(self, path_values:list[str], data:Addable) -> ImmutableTree:

        result = self.deep_clone(self._parent)

        pointer = result

        for path_value in path_values:
            if path_value not in pointer._children:
                pointer._children[path_value] = ImmutableTree(pointer).add_data(path_values, data)
            else:
                pointer = pointer._children[path_value]
        pointer._data += data
        
        return result.prune()
    

    def remove_data(self, node_values:list[str], data:Addable) -> ImmutableTree:
        return self.add_data(node_values, -data)
        # if len(node_values) == 0:
        #     if len(data) == 0:
        #         return self
        #     else:
        #         result = self.deep_clone(self._parent)
        #         result._data -= data
        #         return result
        

        # node_value, *node_values = node_values

        # if node_value in self._children:
        #     result        :ImmutableTree = self.deep_clone(self._parent)
        #     result._children[node_value] = result._children[node_value].remove_data(node_values, data)
        #     if result._children[node_value].is_empty_leaf():
        #         del result._children[node_value]
        #     return result
        
        # return self
    
    def merge(self, other:ImmutableTree) -> ImmutableTree:
        
        if self.is_leaf() and other.is_leaf():
            result = self.deep_clone(self._parent)
            result._data += other._data
            return result
        
        result = self.deep_clone(self._parent)

        if not all(key in other._children for key in self._children):
            raise ImmutableTreeMergeError(f"Cannot merge trees with different node sets: {self} {other}")

        for key, value in other._children.items():
            if key in result._children:
                result._children[key] = result._children[key].merge(value)
            else:
                raise ImmutableTreeMergeError(f"{key} not in subtree {self} of {self.root()}")
        return result

    def map(self, func:Callable) -> ImmutableTree:
        result = self.deep_clone(self._parent)
        result._data = self._data.map(func)
        for key, value in self._children.items():
            result._children[key] = value.map(func)
        return result

    def __str__(self):
        data = ' '.join(str(item) for item in self._data) if len(self._data) > 0 else ''
        children = " ".join(f"{key}:{value}" for key,value in self._children.items())
        joiner = ":" if len(children) > 0 and len(data)>0 else ''
        return f"<{data}{joiner}{children}>"
    

    def __repr__(self):
        return self.__str__()

    def get_leaf_data(self, child_name_path:Optional[list[str]]=None) -> Generator[tuple[list[str], Addable], None, None]:
        child_name_path = [] if child_name_path is None else child_name_path
        if self.is_leaf():
            yield child_name_path, self._data
        else:
            for child_name, child in self._children.items():
                yield from child.get_leaf_data([*child_name_path, child_name])

    def get_row_data(self, child_name_path:Optional[list[str]]=None):
        child_name_path = [] if child_name_path is None else child_name_path
        if self.is_leaf():
            for item in self._data:
                yield child_name_path, item
        else:
            for child_name, child in self._children.items():
                yield from child.get_row_data([child_name, *child_name_path])

    def get_depth(self) -> int:
        if self.is_leaf():
            return 0
        return 1 + max(child.get_depth() for child in self._children.values())

    def as_dataframe(self) -> pd.DataFrame:
        rows = []
        for data in self.get_row_data():
            rows.append([*data[0], *data[1]])
        columns = [f"L{i}" for i in range(self.get_depth())]
        return pd.DataFrame(
            data=rows
        )


def cross_sections(
    segmentation:pd.DataFrame,
    group_categories:list[str],
    cross_section_categories:list[str],
    measure_slk:tuple[str,str],
    measure_true:tuple[str,str],
)->pd.DataFrame:
    
    output_rows = []
    group_counter = 0
    for group_index, group in segmentation.groupby(group_categories):
        
        group = group[[*group_categories, *cross_section_categories, *measure_true, *measure_slk]]#.reset_index(drop=True)

        start_events = group.copy().sort_values(by=cross_section_categories, ascending=True)
        start_events["event_measure"] = start_events[measure_true[0]]
        start_events["event_type"] = "start"
        start_events["event_effect"] = +1
        
        end_events = group.copy().sort_values(by=cross_section_categories, ascending=False)
        end_events["event_measure"] = end_events[measure_true[1]]
        end_events["event_type"] = "end"
        end_events["event_effect"] = -1

        events = pd.concat([end_events, start_events], axis=0).sort_values(by="event_measure", kind="stable")
        events["event_effect_cumsum"] = events["event_effect"].cumsum()
        events["event_measure_diff"] = events["event_measure"].diff().fillna(0)

        past_trees = []
        current_tree = ImmutableTree(None)
        for index, row in events.iterrows():
            if row["event_type"]=="start":
                current_tree = current_tree.add_data(row[cross_section_categories], Addable([(0,index)]))
                past_trees.append(current_tree)
            elif row["event_type"]=="end":
                current_tree = current_tree.remove_data(row[cross_section_categories], Addable([(0, index)]))
                past_trees.append(current_tree)
        events["event_trees"] = [item for item in past_trees]

        transitions = []
        last_index = events.index[0]
        last_row = events.iloc[0]
        for index, row in events.iloc[1:].iterrows():
            if row["event_measure_diff"] > 0:
                transitions.append((last_row["event_measure"], row["event_measure"], last_row["event_trees"]))
            last_index = index
            last_row = row
        
        mapped_transitions:list[tuple[float, float, ImmutableTree]] = [
            (
                measure_from,
                measure_to,
                item.map(lambda item: (item[1], measure_to-measure_from))
            )
            for measure_from, measure_to, item
            in transitions
        ]

        merged_transitions:list[tuple[float,float,ImmutableTree]] = []
        transition_accumulator = mapped_transitions[0]
        for transition in mapped_transitions[1:]:
            measure_from,      measure_to,      tree      = transition
            measure_from_last, measure_to_last, tree_last = transition_accumulator
            try:
                merged_tree = tree_last.merge(tree)
            except ImmutableTreeMergeError:
                merged_transitions.append(transition_accumulator)
                transition_accumulator = transition
                continue
            transition_accumulator = (measure_from_last, measure_to, merged_tree)
        merged_transitions.append(transition_accumulator)
        
        group_index_list = [group_index] if not isinstance(group_index, tuple) else group_index

        for cross_section_number, (measure_from, measure_to, tree) in enumerate(merged_transitions):
            for child_name, child_data in tree.get_leaf_data():
                for child_data_sub in child_data:
                    output_rows.append(new_row:=[
                        group_counter,
                        cross_section_number,
                        *group_index_list,
                        *child_name,
                        measure_from,
                        measure_to,
                        *child_data_sub
                    ])
                    #print(new_row)
    columns = ["group_number", "cross_section_number", *group_categories, *cross_section_categories, *measure_true, "original_index", "overlap"]
    #print(columns)
    return pd.DataFrame(
        data=output_rows,
        columns=columns
    )
           


