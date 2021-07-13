from fmpy.model_description import read_model_description
from fmpy import extract
from fmpy.simulation import instantiate_fmu, simulate_fmu, Input
import numpy as np
import shutil

class FMI_env:
    done = False
    start_values = {}
    _simulation_input = None
    _state = None
    start_time = 0
    stop_time = 0
    tau = 1.
    output = None
    statistic_input = {}
    _counter = 0
    input_names = []
    def __init__(self, fmu_file):
        self.unzipdir = extract(fmu_file)

        # read the model description
        self.model_description = read_model_description(self.unzipdir)
        # instantiate the FMU
        self.fmu_instance = instantiate_fmu(self.unzipdir, self.model_description, 'ModelExchange')
        self.observation_space = self._get_observation_space()
        self.action_space = self._get_action_space()

    def _get_action_space(self):
        pass

    def _get_observation_space(self):
        pass

    def reward(self,action = None, old_state= None):
        if self.failed_simulation:
            return -100.
        if self.done:
            return 1.
        else:
            return -1.
    def reset(self):
        self.failed_simulation = False
        self.done = False
        self._counter = 0
        self.start_time = 0
        self.stop_time = 1. # self.tau
        self.simulation_input= np.array([0.]*(len(self.action_input)),dtype=float)
        self.fmu_instance.reset()
        simulation_result = self.do_simulation()
        self._counter = 1
        self.state = simulation_result
        self.start_time = self.stop_time
        self.stop_time = self.stop_time + self.tau
        return self.state

    @property
    def end(self):
        if self.statistic_input:
            for x in self.statistic_input:
                return len(self.statistic_input[x])
        else:
            return -1

    def step(self, action):
        self.simulation_input = action
        old_state = self.state
        simulation_result= self.do_simulation()
        self.start_time = self.stop_time
        self.stop_time += self.tau
        self._counter += 1
        if self.failed_simulation:
            self.done = True
            return self.state, self.reward(action, old_state), self.done, {}
        if self._counter >= self.end - 1:
            self.done = True
        self.state = simulation_result
        return self.state, self.reward(action, old_state), self.done, {}

    @property 
    def action_input(self):
        return [x for x in self.input_names if x not in self.statistic_input]

    @property 
    def statistic_input(self):
        return list(self.statistic_input.keys())

    @property
    def state(self):
        return self._state

    def transform_state(self,value):
        value  = np.array([x for x in value.values()] + self.current_statistic,dtype=float)
        return value

    @state.setter
    def state(self, value):
        self._state = self.transform_state(value)

    @property
    def current_statistic(self):
        if self.statistic_input:
            return [self.statistic_input[x][self._counter] for x in self.statistic_input] 
        else:
            return []
    @property
    def simulation_input(self):
        return self._simulation_input

    def transform_simulation_input(self,value)-> Input:
        if value is None:
            signals = np.array(
                [tuple([self.start_time] + [x for x in self.current_statistic])],
                dtype = [('time',float)] + [(x,float) for x in self.statistic_input]
                )
        else:
            signals = np.array(
                [tuple([self.start_time] + [x for x in self.current_statistic] + [x for x in value])],
                dtype = [('time',float)] + [(x,float) for x in self.statistic_input] + [(x,float) for x in self.action_input] 
                )
        return signals

    @simulation_input.setter
    def simulation_input(self, value):
        self._simulation_input = self.transform_simulation_input(value)

    def do_simulation(self):
  
        try:
            initialize = True if self._counter == 0 else False
            result = simulate_fmu(
                self.unzipdir,
                start_time=self.start_time,
                stop_time=self.stop_time,
                # input = self.simulation_input,
                output=self.output,
                model_description=self.model_description,
                fmu_instance=self.fmu_instance,
                initialize=initialize
                )
            d = {x : result[x][-1] for x in result.dtype.fields if x!='time'}
            return d
        except Exception as e:
            print(repr(e))
            self.failed_simulation = True
            return 

    def close(self):
        self.fmu_instance.terminate()
        self.fmu_instance.freeInstance()
        shutil.rmtree(self.unzipdir, ignore_errors=True)

    def get_current(self, name):
        x = self.output + list(self.statistic_input.keys())
        return {x[i]:self.state[i] for i in range(len(x))}[name]



