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


def closest(ints, target):
    min_distance = 9999
    min_ele = None

    for i in ints:
        distance = math.fabs(target - i)
        if distance < min_distance and i != target:
            min_distance = distance
            min_ele = i

    return min_ele


def elements_above(ints, target):
    return [x for x in ints if x > target]


def elements_below(ints, target):
    return [x for x in ints if x < target]


class Floor:
    def __init__(self, floornumber):
        self.id = floornumber
        self.current_passengers = []

    def enter(self, passenger):
        self.current_passengers.append(passenger)

    def exit(self, passenger):
        if passenger not in self.current_passengers:
            raise Exception("Tried to exit passenger %d but they were not on floor %d!" % (passenger.id, self.id))

        self.current_passengers.remove(passenger)

    def __str__(self):
        return "Floor %d [Current passengers: [%s]]" % (
            self.id, ", ".join([str(x.id) for x in self.current_passengers]))

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
        self.current_floor = 0
        self.current_passengers = []
        self.direction = Elevator.STATIONARY
        # elevator keeps this state to know where to stop along the way
        self.pending_stops = []

    def has_room(self):
        return len(self.current_passengers) < self.capacity

    def board(self, passenger):
        if len(self.current_passengers) + 1 > self.capacity:
            raise Exception("Elevator %d attempted to load over capacity!" % self.id)

        self.current_passengers.append(passenger)

    def depart(self, passenger):
        if passenger not in self.current_passengers:
            raise Exception("Tried to exit passenger %d but they were not in elevator %d!" % (passenger.id, self.id))

        self.current_passengers.remove(passenger)

    def add_stop(self, stop):
        if stop not in self.pending_stops:
            self.pending_stops.append(stop)
            self.pending_stops = sorted(self.pending_stops)

    def __str__(self):
        return "Elevator %d [Current floor %d, direction %s, pending stops [%s]]" % (
            self.id, self.current_floor, Elevator.get_direction_string(self.direction),
            ", ".join([str(x) for x in self.pending_stops]))

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


class SimEvent:
    class SimEvents:
        BOARD = 1
        DEPART = 2
        ELE_MOVE = 3

        @classmethod
        def to_str(cls, event):
            if event == cls.BOARD:
                return "board"
            elif event == cls.DEPART:
                return "depart"
            elif event == cls.ELE_MOVE:
                return "move"
            else:
                return "unknown"

    def __init__(self, event, data):
        self.event = event
        self.data = data

    def __eq__(self, other):
        return self.data == other.data and self.event == other.event

    def __str__(self):
        return "%s - %s" % (SimEvent.SimEvents.to_str(self.event), self.data)


class Simulation:
    def __init__(self, elevator_capacity, num_elevators, num_floors, passengers):
        self.sim_step = 0

        self.elevator_capacity = elevator_capacity

        self.floors = [Floor(x) for x in range(num_floors)]
        self.elevators = [Elevator(self.elevator_capacity) for _ in range(num_elevators)]
        self.passengers = passengers[:]
        # list of all stops pending on all elevators, to avoid duplicating destinations
        self.global_pending_stops = []
        # list of events triggered by sim, useful record for testing
        self.sim_events = []

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

    @classmethod
    def manual_setup(cls, elevator_capacity, num_elevators, num_floors, passengers):
        return cls(elevator_capacity, num_elevators, num_floors, passengers)

    @classmethod
    def random_setup(cls, elevator_capacity, num_elevators, num_passengers, num_floors):
        passengers = []

        for i in range(num_passengers):
            temp = [x for x in range(num_floors)]

            start_floor = temp.pop(random.randint(0, len(temp) - 1))
            end_floor = temp.pop(random.randint(0, len(temp) - 1))

            passengers.append(Passenger(start_floor, end_floor))

        return cls(elevator_capacity, num_elevators, num_floors, passengers)

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
            floor_requests = []

            for floor in self.floors:
                if len(floor.current_passengers):
                    # if at least one passenger is idle on a floor, they are requesting an elevator goes there
                    print("Elevator requested on floor %d" % floor.id)
                    floor_requests.append(floor.id)

                # board into any elevators that are stopped at this floor
                # only board passengers who wish to go the direction of the elevator
                # e.g. if a passenger is on floor 3, and wants to go to floor 1, only board DOWN elevators
                for elevator in self.elevators:
                    if elevator.current_floor == floor.id:
                        boarded_passengers = []

                        for passenger in floor.current_passengers:
                            # determine desired direction
                            if passenger.destination > floor.id:
                                desired_direction = Elevator.UP
                            elif passenger.destination < floor.id:
                                desired_direction = Elevator.DOWN
                            else:
                                raise Exception("Passenger should not be on the floor they wish to exit on!")

                            if elevator.has_room() and (
                                    elevator.direction == desired_direction or
                                    elevator.direction == Elevator.STATIONARY):

                                print("Boarding passenger %d in elevator %d (on floor %d,"
                                      " desired destination %d, elevator direction %s)" %
                                      (passenger.id, elevator.id, floor.id, passenger.destination,
                                       Elevator.get_direction_string(elevator.direction)))
                                self.put_sim_event(SimEvent.SimEvents.BOARD, passenger.id)

                                elevator.board(passenger)
                                if passenger.destination not in self.global_pending_stops:
                                    elevator.add_stop(passenger.destination)
                                    self.global_pending_stops.append(passenger.destination)
                                # make sure the passenger is not in two places at once
                                boarded_passengers.append(passenger)
                        # exit after processing all passengers
                        [floor.exit(x) for x in boarded_passengers]

            # elevator is loaded with new passengers from floor
            # now, determine where elevators should go based on:
            # current location
            # internal passenger destinations
            # open requests
            # pending stops
            for elevator in self.elevators:
                # if any passenger is on their desired floor, they depart
                for passenger in elevator.current_passengers:
                    if elevator.current_floor == passenger.destination:
                        print("@@@ Passenger %d is departing (on floor %d, destination %d)" % (
                            passenger.id, elevator.current_floor, passenger.destination
                        ))
                        self.put_sim_event(SimEvent.SimEvents.DEPART, passenger.id)
                        elevator.depart(passenger)
                        self.passengers.remove(passenger)

                        if len(self.passengers) == 0:
                            self.sim_end()
                            return self.sim_events

                if len(elevator.pending_stops) == 0:
                    # reset direction as we can now choose which way to go again
                    elevator.direction = Elevator.STATIONARY

                # remove stops from this list that the elevator shouldn't go to
                # e.g. if the elevator is heading towards floor 1 for a request, it should not pick up on floor 2
                # before handling that person's request
                if elevator.direction == Elevator.STATIONARY:
                    if len(elevator.current_passengers):
                        # take the first person's destination, that is the new direction
                        stop = elevator.current_passengers[0].destination
                    else:
                        # pick the first request to take direction, pick all stops along that way
                        stop = closest(floor_requests, elevator.current_floor)

                    if stop is None:
                        self.sim_end()
                        return self.sim_events

                    print("Elevator %d  floor %d is stationary, picking stop %d" % (
                        elevator.id, elevator.current_floor, stop))
                    if stop > elevator.current_floor:
                        elevator.direction = Elevator.UP
                        floor_requests = [x for x in floor_requests if x <= stop]
                    else:
                        elevator.direction = Elevator.DOWN
                        floor_requests = [x for x in floor_requests if x >= stop]
                    print("New direction %s" % elevator.get_direction_string(elevator.direction))

                # at this point, the elevator should have a direction
                if elevator.direction == Elevator.UP:
                    # look ahead to pick up any requests on the way to our destination
                    requested_floors = [x for x in floor_requests if x > elevator.current_floor] + [
                        x for x in [y.destination for y in elevator.current_passengers] if x > elevator.current_floor]

                elif elevator.direction == Elevator.DOWN:
                    # do the same, looking down instead
                    requested_floors = [x for x in floor_requests if x < elevator.current_floor] + [
                        x for x in [y.destination for y in elevator.current_passengers] if x < elevator.current_floor]

                else:
                    raise Exception("Elevator does not have a direction after checking requests!")

                if len(requested_floors) > 0:
                    sorted_floors = sorted(requested_floors)
                    [elevator.add_stop(x) for x in sorted_floors if x not in self.global_pending_stops]
                    [self.global_pending_stops.append(x) for x in sorted_floors if x not in self.global_pending_stops]

                # move every elevator to their first pending stop
                if len(elevator.pending_stops) > 0:
                    elevator.current_floor = elevator.pending_stops.pop(0)
                    self.global_pending_stops.remove(elevator.current_floor)
                    print("Elevator %d moved to floor %d" % (elevator.id, elevator.current_floor))
                    self.put_sim_event(SimEvent.SimEvents.ELE_MOVE,
                                       {"elevator_id": elevator.id, "floor": elevator.current_floor})

                    # if now the elevator has reached its final stop, we're stationary again
                    if not len(elevator.pending_stops):
                        elevator.direction = Elevator.STATIONARY

            print("***********************************")
            print(self)
            self.sim_step += 1

        return self.sim_events

    def sim_end(self):
        print("Simulation finished after %d steps" % self.sim_step)

    def put_sim_event(self, event, data):
        self.sim_events.append({
            "step": self.sim_step,
            "sim_event": SimEvent(event, data)
        })

# TODO multi elevator bugs:
# runs finish too early sometimes (see txt file)
# passengers on same floor are getting split between elevators for some reason, when they could fit in 1

if __name__ == '__main__':
    for z in range(0, 1):
        s = Simulation.random_setup(5, 2, 5, 3)
        print(s)
        s.sim_loop()
        print("Finished sim run %d" % z)
