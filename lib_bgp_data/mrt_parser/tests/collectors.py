import enum

# File to hold some collectors for testing use, to keep the tester code clean
class Collectors(enum.Enum):
    collectors_0 = []
    collectors_1 = {"collectors[]": ["route-views2"]}
    collectors_2 = {"collectors[]": ["route-views.telxatl", 
                                     "route-views2"]}
    collectors_3 = {"collectors[]": ["route-views.telxatl",
                                     "route-views2",
                                     "route-views6"]}
