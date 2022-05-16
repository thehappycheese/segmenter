from __future__ import annotations
from typing import Callable, Collection, Optional, Hashable
import pandas as pd


class ImmutableTree:
    """
    This is not a very clever implementation of a Tree storage structure.
    It was cobbled together as the while itterating on the algorithm.
    It is intended to be replaced with a refactored version.
    """
    __slots__ = '_parent', '_children', '_data'

    _parent:Optional[ImmutableTree]
    _children:dict[str, ImmutableTree]
    _data:set
    

    def __init__(self, parent:Optional[ImmutableTree]):
        self._parent = parent
        self._children = {}
        self._data      = set()
    
    def root(self) -> ImmutableTree:
        if self._parent is None:
            return self
        return self._parent.root()

    def is_leaf(self) -> bool:
        return self._children == {}
    
    def is_empty_leaf(self) -> bool:
        return self._children == {} and self._data == set()

    def deep_clone(self, new_parent:Optional[ImmutableTree]) -> ImmutableTree:
        clone = ImmutableTree(new_parent)
        clone._data = self._data.copy()
        for key, value in self._children.items():
            clone._children[key] = value.deep_clone(clone)
        return clone

    def add_data(self, path_values:list[str], data:Collection[Hashable]) -> ImmutableTree:
        if len(path_values) == 0:
            if len(data) == 0:
                return self
            else:
                result = self.deep_clone(self._parent)
                result._data.update(data)
                return result

        

        path_value, *path_values = path_values

        result        :ImmutableTree = self.deep_clone(self._parent)
        if path_value not in result._children:
            result._children[path_value] = ImmutableTree(result).add_data(path_values, data)
        else:
            result._children[path_value] = result._children[path_value].add_data(path_values, data)

        return result
    

    def remove_data(self, node_values:list[str], data:Collection[Hashable]) -> ImmutableTree:
        if len(node_values) == 0:
            if len(data) == 0:
                return self
            else:
                result = self.deep_clone(self._parent)
                result._data.difference_update(data)
                return result
        

        node_value, *node_values = node_values

        if node_value in self._children:
            result        :ImmutableTree = self.deep_clone(self._parent)
            result._children[node_value] = result._children[node_value].remove_data(node_values, data)
            if result._children[node_value].is_empty_leaf():
                del result._children[node_value]
            return result
        
        return self
    
    def merge(self, other:ImmutableTree) -> ImmutableTree:
        
        if self.is_leaf() and other.is_leaf():
            result = self.deep_clone(self._parent)
            result._data.update(other._data)
            return result

        result = self.deep_clone(self._parent)
        for key, value in other._children.items():
            if key in result._children:
                result._children[key] = result._children[key].merge(value)
            else:
                raise Exception(f"{key} not in subtree {self} of {self.root()}")
        return result

    def map(self, func:Callable) -> ImmutableTree:
        result = self.deep_clone(self._parent)
        result._data = set(func(item) for item in self._data)
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


def iterate_over_cross_sections(
    segmentation:pd.DataFrame,
    group_categories:list[str],
    cross_section_categories:list[str],
    measure_slk:tuple[str,str],
    measure_true:tuple[str,str],
):

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
                current_tree = current_tree.add_data(row[cross_section_categories], [index])
                past_trees.append(current_tree)
            elif row["event_type"]=="end":
                current_tree = current_tree.remove_data(row[cross_section_categories], [index])
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
        
        mapped_transitions = [
            (
                group_index
                measure_from,
                measure_to,
                item.map(lambda item: (item, measure_to-measure_from))
            )
            for measure_from, measure_to, item
            in transitions
        ]

        # merged_transitions = []
        # for i in range(0, len(transitions)):
        #     pass



    return events, mapped_transitions


