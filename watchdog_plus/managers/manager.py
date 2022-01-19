from .errors import ServiceNotFound


class Manager:
    def get_by_name(self, name, collection):
        """Returns an observer by it's name"""
        try:
            item = [i for i in collection if i.name == name][0]
        except IndexError:
            raise ServiceNotFound(f"no service with name {name} exists")
        return item

    def generate_name(self, path) -> str:
        """Generates name for path"""
        name = path.strip("/").split("/")[-1]
        return name

    def generate_names(self, paths):
        """Generates names for paths and also
        keeps track of the position of each name"""
        names, position_data, pos = list(), dict(), -1
        for path_ in paths:
            name = self.generate_name(path_)
            while name in names:
                pos -= 1
                name = self.generate_name(path_.removesuffix(f"/{name}"))
            names.append(name)
            position_data[name] = pos
        # write position data to file
        self.write_positions(position_data)
        # return names
        return names
