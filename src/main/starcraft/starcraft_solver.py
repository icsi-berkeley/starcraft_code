"""

Author: vivekraghuram <vivek.raghuram@berkeley.edu>

A StarcraftProblemSolver that extends the CoreProblemSolver in the NLUAS module.

Actions, like "move", should be named by predicate + action type.
Thus: query_move, command_move, etc.
Or: query_be, command_be, etc.

"""

from nluas.app.core_solver import *
from nluas.utils import *
import sys
from threading import Thread, Lock
from nluas.Transport import Transport
import json
import time
from pprint import pprint

import os
dir_name = os.path.dirname(os.path.realpath(__file__))

class BasicStarcraftProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self.headings = dict(north=(0.0, 1.0, 0.0), south=(0.0, -1.0, 0.0),
                    east=(1.0, 0.0, 0.0), west=(-1.0, 0.0, 0.0))

        self._inputs = []
        self._lock = Lock()
        self._game_started = False
        self._verbose = True

        self._response = None
        self.adapter_address = "StarCraft"
        self.transport.subscribe(self.adapter_address, self.adapter_callback)
        self.adapter_templates = self.read_templates(
            os.path.join(dir_name, "adapter_templates.json"))

    def read_templates(self, filename):
        """ Sets each template to ordered dict."""
        base = OrderedDict()
        with open(filename, "r") as data_file:
            data = json.load(data_file, object_pairs_hook=OrderedDict)
            for name, template in data['templates'].items():
                base[name] = template
        return base

    def callback(self, actspec):
        """
        Called asychronously when an actspec is available from the specializer. Adds it to a
        queue of inputs.
        """
        if self._verbose:
            print("Received ActSpec:")
            pprint(actspec)
        if self.is_quit(actspec):
            return self.close()
        with self._lock:
            self._inputs.append(actspec)

    def adapter_callback(self, response):
        """
        Called asychronously when a response is sent from the game. Adds it to a
        queue of game responses.
        """
        if self._verbose:
            print("Recieved adapter response:")
            pprint(response)
        with self._lock:
            self._response = response

    def solve(self):
        """
        Checks the input queue and inserts any pending inputs to the conditions data structure.
        Executes conditions once all inputs have been processed.
        """
        if not self._game_started:
            self._game_started = self.is_started()
            if self._game_started and self._verbose:
                print("Connected to StarCraft game")
            else:
                return

        completed = []
        for index, actspec in enumerate(self._inputs):
            predicate_type = actspec['predicate_type']
            try:
                dispatch = getattr(self, "solve_%s" %predicate_type)
                dispatch(actspec)
                completed.insert(0, index)
            except AttributeError as e:
                traceback.print_exc()
                message = "I cannot solve a(n) {}.".format(predicate_type)
                self.identification_failure(message)
            except RuntimeWarning as e:
                print(e)
            except RuntimeError as e:
                traceback.print_exc()
                completed.insert(0, index)
        for index in completed:
            del self._inputs[index]

    def adapter_command(self, message, timeout=5):
        """
        Sends message to the adapter and waits for a response
        """
        self.validate_message(message)

        send_time = time.time()
        self._response = None
        self.transport.send(self.adapter_address, json.dumps(message))

        if self._verbose:
            print("Sent to adapter:")
            pprint(message)

        while time.time() - send_time <= timeout:
            if self._response:
                if self._verbose:
                    print("received:")
                    pprint(self._response)
                return self._response
            time.sleep(1.0 / 24.0) # Shortest length of a frame
        raise RuntimeError("Command timed out: " + str(message))

    def is_started(self):
        """
        Determines whether the game has begun
        """
        message = dict(self.adapter_templates["is_started"])
        try:
            response = self.adapter_command(message)
        except RuntimeError as e:
            return False
        return bool(response)

    def command_build(self, parameters):
        """
        Tells the game to build an object
        """
        message = dict(self.adapter_templates["build"])
        obj = parameters['createdThing']['objectDescriptor'] #shouldn't this just be 'descriptor'?
        message["quantity"] = self.get_quantity(obj)
        message["unit_type"] = self.get_type(obj)

        response = self.adapter_command(message)
        if response["status"] == "failed":
            remaining = int(response["remaining"])
            if obj['number'] == "plural":
                obj['quantity']['amount']['value'] = remaining
            raise RuntimeWarning("Not able to build all units. %d units remaining" %remaining)

    def command_gather(self, parameters):
        """
        Tells the game to build an object
        """
        message = dict(self.adapter_templates["gather"])
        obj = parameters['resource']['objectDescriptor'] #shouldn't this just be 'descriptor'?
        message["resource_type"] = self.get_type(obj)

        response = self.adapter_command(message)
        if response["status"] == "failed":
            raise RuntimeWarning("Not able to gather %s" %message["resource_type"])


    def get_quantity(self, objectDescriptor):
        if objectDescriptor['number'] == "plural":
            return int(objectDescriptor['quantity']['amount']['value'])
        return 1

    def get_type(self, objectDescriptor):
        return objectDescriptor['type']

    def solve_serial(self, parameters, predicate):
        """
        Solves a serial event
        """
        self.route_action(parameters['process1'], predicate)
        self.route_action(parameters['process2'], predicate)

    def solve_command(self, actspec):
        """
        Solves a command
        """
        parameters = actspec['eventDescriptor']
        self.route_event(parameters, "command")

    def validate_message(self, message):
        template = self.adapter_templates[message["action"]]

        for k, v in template.items():
            if k == "action":
                pass
            elif v == "INTEGER" and isinstance(message[k], int):
                pass
            elif v == "STRING" and isinstance(message[k], str):
                pass
            else:
                raise RuntimeError("Invalid message: %s" %message)


if __name__ == "__main__":
    solver = BasicStarcraftProblemSolver(sys.argv[1:])
    solver.keep_alive(solver.solve)
