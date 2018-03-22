# ELEVATOR SIMULATOR
# *--
# |
# |   Floor 3
# |
# *--
#
#
#
# *--
# |
# |   Floor 2
# |
# *--
#
#
#
# *--
# |
# |   Ground floor (1)
# |
# *--
#
# Elevators work in a request -> move -> board -> request loop
# The move will aim to empty the elevator of passengers while picking up new ones in an efficient plan

import random

import math


# todo probably a library func for this
def closest(ints, target):
    min_distance = 9999
    min_ele = None

    for i in ints:
        distance = math.fabs(target - i)
        if distance < min_distance:
            min_distance = distance
            min_ele = i

    return min_ele

def elements_above(ints, target):
    return [x for x in ints if x > target]


def elements_below(ints, target):
    return [x for x in ints if x < target]

class Floor:
    # running counter of all floor IDs
    curr_id = 0

    @classmethod
    def get_new_id(cls):
        i = cls.curr_id
        cls.curr_id += 1

        return i

    def __init__(self):
        self.id = Floor.get_new_id()
        self.current_passengers = []

    def enter(self, passenger):
        self.current_passengers.append(passenger)

    def exit(self, passenger):
        if passenger not in self.current_passengers:
            raise Exception("Tried to exit passenger %d but they were not on floor %d!" % (passenger.id, self.id))

        self.current_passengers.remove(passenger)

    def __str__(self):
        return "Floor %d [Current passengers: [%s]]" % (self.id, ", ".join([str(x.id) for x in self.current_passengers]))

    def __hash__(self):
        return self.id


class Elevator:
    # running counter of all elevator IDs
    curr_id = 0

    # directions elevator can travel
    # elevators "in motion" or with a destination in mind are represented
    # by a direction != STATIONARY
    UP = 1
    DOWN = 2
    STATIONARY = 3

    @staticmethod
    def get_direction_string(direction):
        if direction == Elevator.UP:
            return "up"
        elif direction == Elevator.DOWN:
            return "down"
        elif direction == Elevator.STATIONARY:
            return "stationary"
        else:
            raise Exception("Unknown direction %d" % direction)

    @classmethod
    def get_new_id(cls):
        i = cls.curr_id
        cls.curr_id += 1

        return i

    def __init__(self, capacity):
        self.id = Elevator.get_new_id()
        self.capacity = capacity
        self.current_floor = 1
        self.current_passengers = []
        self.direction = Elevator.STATIONARY
        # elevator keeps this state to know where to stop along the way
        self.pending_stops = set()

    def has_room(self):
        return len(self.current_passengers) < self.capacity

    def board(self, passenger):
        if len(self.current_passengers) + 1 >= self.capacity:
            raise Exception("Elevator %d attempted to load over capacity!" % self.id)

        self.current_passengers.append(passenger)

    def depart(self, passenger):
        if passenger not in self.current_passengers:
            raise Exception("Tried to exit passenger %d but they were not in elevator %d!" % (passenger.id, self.id))

        self.current_passengers.remove(passenger)

    def add_stop(self, stop):
        self.pending_stops.append(stop)

    def __str__(self):
        return "Elevator %d [Current floor %d, direction %s]" % (
            self.id, self.current_floor, Elevator.get_direction_string(self.direction))

    def __hash__(self):
        return self.id


class Passenger:
    # running counter of all passenger IDs
    curr_id = 0

    @classmethod
    def get_new_id(cls):
        i = cls.curr_id
        cls.curr_id += 1

        return i

    def __init__(self, start_floor, destination_floor):
        self.id = Passenger.get_new_id()
        self.start = start_floor
        self.destination = destination_floor

    def __str__(self):
        return "Passenger %d [Start %d, destination %d]" % (self.id, self.start, self.destination)

    def __hash__(self):
        return self.id


class Simulation:
    # actions
    ENTER = 1
    EXIT = 2
    WAIT = 3

    def __init__(self, elevator_capacity, num_elevators, num_passengers, num_floors):
        self.sim_step = 0

        self.elevator_capacity = elevator_capacity

        self.floors = [Floor() for _ in range(num_floors)]
        self.elevators = [Elevator(self.elevator_capacity) for _ in range(num_elevators)]
        self.passengers = []

        for i in range(num_passengers):
            temp = [x.id for x in self.floors[:]]

            start_floor = temp.pop(random.randint(0, len(temp) - 1))
            end_floor = temp.pop(random.randint(0, len(temp) - 1))

            self.passengers.append(Passenger(start_floor, end_floor))

        # load floors with initial passengers
        for passenger in self.passengers:
            # todo temp temp
            start_floor = None
            for floor in self.floors:
                if floor.id == passenger.start:
                    start_floor = floor
            # desired_floor = self.floors[self.floors.index(passenger.destination)]

            if start_floor is None:
                raise Exception("Could not find start floor %d for passenger %d" % (
                    passenger.destination, passenger.id))

            start_floor.enter(passenger)

    def __str__(self):
        to_return = "[Simulation] Passengers: %d, Floors: %d, Elevators: %d\n" % (
            len(self.passengers), len(self.floors), len(self.elevators))

        to_return += "Passengers: ["
        for passenger in self.passengers:
            to_return += "\n\t" + str(passenger)

        to_return += "\n]\n"

        to_return += "Elevators: ["
        for elevator in self.elevators:
            to_return += "\n\t" + str(elevator)

        to_return += "\n]\n"

        to_return += "Floors: ["
        for floor in self.floors:
            to_return += "\n\t" + str(floor)

        to_return += "\n]\n"

        return to_return

    def sim_loop(self):
        while len(self.passengers) > 0:
            print("Sim step %d" % self.sim_step)
            floor_requests = {}

            for floor in self.floors:
                # first collect requests for the floor
                requests = set()

                for passenger in floor.current_passengers:
                    # if a passenger is idle on a floor, they are requesting to be picked up
                    requests.add(passenger)

                floor_requests[floor.id] = requests

                # board into any elevators that are stopped at this floor
                # only board passengers who wish to go the direction of the elevator
                # e.g. if a passenger is on floor 3, and wants to go to floor 1, only board DOWN elevators
                for elevator in self.elevators:
                    if elevator.current_floor == floor.id:
                        for passenger in floor.current_passengers:
                            # determine desired direction
                            if passenger.destination > floor.id:
                                desired_direction = Elevator.UP
                            elif passenger.destination < floor.id:
                                desired_direction = Elevator.DOWN
                            else:
                                # this passenger is done, let's remove them
                                print("Passenger %d is departing (on floor %d, destination %d)" % (
                                    passenger.id, elevator.current_floor, passenger.destination
                                ))
                                elevator.depart(passenger.id)
                                self.passengers.remove(passenger)
                                continue

                            if elevator.has_room() \
                                    and (elevator.direction == desired_direction
                                         or elevator.direction == Elevator.STATIONARY):

                                print("Boarding passenger %d in elevator %d (on floor %d,"
                                      " desired destination %d, elevator direction %s)" %
                                      (passenger.id, elevator.id, floor.id, passenger.destination,
                                       Elevator.get_direction_string(elevator.direction)))

                                elevator.board(passenger)
                                elevator.add_stop(passenger.destination)
                                # make sure the passenger is not in two places at once
                                floor.exit(passenger)

            # elevator is loaded with new passengers from floor
            # now, determine where elevators should go based on:
            # current location
            # internal passenger destinations
            # open requests
            # pending stops -- an elevator will only have pending stops when it is nonempty
            for elevator in self.elevators:
                if len(elevator.pending_stops) == 0:
                    # reset direction as we can now choose which way to go again
                    elevator.direction = Elevator.STATIONARY

                if len(elevator.pending_stops) and len(elevator.current_passengers) == 0:
                    raise Exception("Assumption that elevator has pending stops only when nonempty is violated!")

                    # # closest open request is the direction we take
                    # TODO i don't feel this is needed, we can just scoop up requests for a direction
                    # elevator.current_floor = closest(floor_requests.keys(), elevator.current_floor)

                # need to associate pending requests with passengers in this current elevator
                if elevator.direction == Elevator.STATIONARY:
                    # pick the first request to take direction, pick all stops along that way
                    closest_stop = closest(floor_requests.keys(), elevator.current_floor)

                    if closest_stop > elevator.current_floor:
                        elevator.direction = Elevator.UP
                    else:
                        elevator.direction = Elevator.DOWN
                # at this point, the elevator should have a direction
                if elevator.direction == Elevator.UP:
                    # look ahead to pick up any requests on the way to our destination
                    requested_floors = [x for x in floor_requests.keys() if x > elevator.current_floor]

                elif elevator.direction == Elevator.DOWN:
                    # do the same, looking down instead
                    requested_floors = [x for x in floor_requests.keys() if x < elevator.current_floor]

                else:
                    raise Exception("Elevator does not have a direction after checking requests!")

                if len(requested_floors) > 0:
                    sorted_floors = sorted(requested_floors)
                    [elevator.pending_stops.add(x) for x in sorted_floors]

            self.sim_step += 1


if __name__ == '__main__':
    s = Simulation(5, 1, 5, 3)
    print(s)
    s.sim_loop()
