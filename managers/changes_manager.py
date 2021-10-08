import json
import re


def load_positions(file) -> dict:
    with open(file) as positions_r:
        data = json.load(positions_r)
    return data


def load_file(file) -> dict:
    """ Loads and return data from analysis file as a dict"""
    with open(file) as analysis_file_r:
        data = json.load(analysis_file_r)
    return data


def get_all_paths(data) -> list:
    """ Returns all the paths in the analysis file. """
    return [path for paths in data.values() for path in paths]


def search_path(query, paths) -> list:
    """ Searches all paths in the event_type for matches with query.
    if the data is the analysis file then event_type must be set otherwise
    you can
    """
    # make a search pattern
    pattern = re.compile(f"{query}", re.I)
    # filter results
    if paths:
        result = list(filter(lambda x: re.search(pattern, x), paths))
        return result
    else: return list() # return empty list


def get_by_name(name, paths, position=None) -> list:
    """
    Returns all the event logs associated to an observer 
    It does this by searching all the list of paths in the paths argument
    but this can inaccurate since any path can contain the name. This
    problem is taken care of by comparing the string at the position 
    the name was taken with the name.

    Returns the raw search if position is not provided.
    """
    results = []
    # get all matching paths first
    for path_list in paths:
        results += search_path(name, path_list)
    data = {} # data to return
    if position:
        for path in results:
            # if the name matches with the position from the logger 
            if path.strip('/').split('/')[position] == name:
                data.setdefault(name, set()).add(path) # append all matches to name
        return data
    return results

