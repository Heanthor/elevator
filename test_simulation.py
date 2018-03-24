from unittest import TestCase

from elevator import Passenger, Simulation, SimEvent


class TestSimulation(TestCase):
    def test_single_elevator(self):
        passengers = [
            Passenger(0, 2),
            Passenger(1, 2),
            Passenger(1, 0),
            Passenger(2, 1),
            Passenger(2, 0)
        ]

        s = Simulation.manual_setup(5, 1, 3, passengers)
        events = s.sim_loop()

        assert check_passenger_movement(passengers, events)

    def test_multiple_elevators(self):
        passengers = [
            Passenger(2, 0),
            Passenger(0, 2),
            Passenger(0, 1),
            Passenger(0, 2),
            Passenger(0, 2)
        ]

        s = Simulation.manual_setup(5, 2, 3, passengers)
        events = s.sim_loop()

        assert check_passenger_movement(passengers, events)

    def test_large_random(self):
        s = Simulation.random_setup(5, 10, 500, 25)
        passengers = s.passengers
        events = s.sim_loop()

        assert check_passenger_movement(passengers, events)


def check_passenger_movement(passengers, events):
    done_passengers = []

    for passenger in passengers:
        for e in events:
            if e["sim_event"].event == SimEvent.SimEvents.DEPART:
                done_passengers.append(passenger.id)

    return sorted([x.id for x in passengers]) != sorted(done_passengers)
