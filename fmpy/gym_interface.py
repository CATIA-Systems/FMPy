import numpy as np
from typing import List, Optional
from pydantic import BaseModel
from fmpy import supported_platforms
from fmpy.model_description import read_model_description
from fmpy.simulation import auto_interval, extract, apply_start_values, Recorder, Input, current_time, platform, ForwardEuler
from fmpy.fmi1 import FMU1Slave, FMU1Model,  fmi1True, fmi1False
from fmpy.fmi2 import FMU2Slave, FMU2Model, fmi2True, fmi2False
from fmpy.fmi3 import FMU3Slave, FMU3Model
from fmpy.sundials import sundials_cvode
import os
import shutil
from gym import Env 
from typing import Dict, List, Optional
from pydantic.main import BaseModel
from pydantic import validator

class FmiEnv(Env):
    _state = None
    input = None
    start = 0
    stop = 0 
    tau = 0
    positive_reward  = 1.
    negative_reward = -1.
    done = True
    _failed_simulation = False
        
    @property
    def state(self):
        """return current state

        Returns
        -------
        np.array
            the current state
        """
        return self._state

    @state.setter
    def state(self, value):
        """set the state by giving a simulation result
        """
        self._state = self._transform_state(value)

    def _get_action_space(self):
        """get the action space of the environment
        """
        pass

    def _get_observation_space(self):
        """get the observation space from the environment
        """
        pass

    def reset(self):
        """reset the simulation game

        Returns
        -------
        np.array
            the zeroth state of the simulated system
        """
        pass

    def do_simulation(self)-> None:
        """do a simulation according to the current state and input to produce a new state
        """
    
        pass

    def _is_done(self):
        """get, if the simulation is done

        Returns
        -------
        bool
            is the simualtion done
        """
        return True
    def _get_input(self,action):
        """helper function to generate input for a given action and time.
        This method may be overwritten to input forecasted data or something like that,
        which is not part of the action, but part of the statistics of the runtime process  
        Parameters
        ----------
        action : np.array

        """
        pass
    
    def _transform_state(self, state):
        """tranform the current simulation result to the next state/ observation
        for example add statistical data...
        Parameters
        ----------
        value : np.array
            simulation result

        Returns
        -------
        np.array
            the actual state, the observation of the agent
        """
        return state

    def step(self, action):
        """do a simulation step in the game according to the current action

        Parameters
        ----------
        action : np.array
            actionin the game

        Returns
        -------
        state : np.array
            the new state
        reward : float
            the reward gained during the step
        done : bool
            is the game over
        info : dict
            info about the simulation step
        """
        last_state = self.state
        if not isinstance(action,np.ndarray):
            raise TypeError("action has to be numpy array")
        self.input = self._get_input(action)
        try:
            self.do_simulation()
        except Exception as e:
            print(repr(e))
            self._failed_simulation = True
        # Check if experiment has finished
        self.done = self._is_done()
        # Move simulation time interval if experiment continues
        if not self.done:
            self.time = self.stop
            self.stop += self.tau

        return self.state, self._reward_policy(action, last_state), self.done, {}


    def _reward_policy(self, action = None, last_state = None):
        """determine the reward *after* applying an action

        Parameters
        ----------
        action : np.array, optional
            the action which shall be performed on the environment, by default None
        last_state : np.array, optional
            the state of the environment before appying the action, by default None

        Returns
        -------
        float
            the reward for the agent for performing the action
        """
        if self._is_done():
            return self.negative_reward
        else:
            return  self.positive_reward
        
    def close(self):
        """close the environment gracefully: terminate the fmi
        """
        pass


_CONF = {
     'time_step': 60.,
     'model_input_names':None,
     'model_output_names':None,
     'model_parameters':None,
     'positive_reward':1.,
     'negative_reward':-1.
     }


class MeSimulationConf(BaseModel):
    """cofiguration class for MeFMI
    """
    time_step = 60.
    model_input_names: Optional[List[str]] = None 
    model_output_names : Optional[List[str]] = None 
    model_parameters : Optional[dict] = None
    positive_reward = 1.
    negative_reward = -1.
class MeFMI(FmiEnv):
    """gym FMI wrapper for model exchange
    """
    def __init__(
            self,
            filename,
            validate=True,
            start_time=None,
            stop_time=None,
            solver='CVode',
            step_size=None,
            relative_tolerance=None,
            output_interval=None,
            record_events=True,
            fmi_type=None,
            use_source_code=False,
            start_values={},
            apply_default_start_values=False,
            input=None,
            output=None,
            timeout=None,
            debug_logging=False,
            logger=None,
            fmi_call_logger=None,
            step_finished=None,
            model_description=None,
            config = MeSimulationConf()
        ):
       
   
        # if you reward policy is different from just reward/penalty - implement custom step method
        self.positive_reward = config.positive_reward
        self.negative_reward = config.negative_reward
        self.output = output 
        # Parameters required by this implementation
        self.tau = config.time_step
        self.model_input_names = config.model_input_names
        self.output = config.model_output_names
        self.model_parameters = config.model_parameters
        self.solver_name = solver
        self.eps = 1e-13
        self._state = None
        self.start_values = start_values
        self.timeout = timeout
        self.record_events  = record_events
        self.step_size = step_size
        self.input_signals = input
        self.time = start_time


        self.action_space = self._get_action_space()
        self.observation_space = self._get_observation_space()

        self.metadata = {
            'render.modes': ['human', 'rgb_array'],
            'video.frames_per_second': 50
        }
        from fmpy import supported_platforms
        from fmpy.model_description import read_model_description

        if not use_source_code and platform not in supported_platforms(filename):
            raise Exception("The current platform (%s) is not supported by the FMU." % platform)

        if model_description is None:
            self.model_description = read_model_description(filename, validate=validate)
        else:
            self.model_description = model_description

        experiment = self.model_description.defaultExperiment

        if start_time is None:
            if experiment is not None and experiment.startTime is not None:
                start_time = experiment.startTime
            else:
                start_time = 0.0
        self.start = start_time
        self.stop = start_time + self.tau
        if relative_tolerance is None and experiment is not None:
            relative_tolerance = experiment.tolerance

        if step_size is None:
            total_time = self.tau
            self.step_size = 10 ** (np.round(np.log10(total_time)) - 3)

        if os.path.isfile(os.path.join(filename, 'modelDescription.xml')):
            unzipdir = filename
            tempdir = None
        else:
            tempdir = extract(filename)
            unzipdir = tempdir

        # common FMU constructor arguments
        fmu_args = {'guid': self.model_description.guid,
                    'unzipDirectory': unzipdir,
                    'instanceName': None,
                    'fmiCallLogger': fmi_call_logger}

        if use_source_code:

            from fmpy.util import compile_dll

            # compile the shared library from the C sources
            fmu_args['libraryPath'] = compile_dll(model_description=self.model_description,
                                                sources_dir=os.path.join(unzipdir, 'sources'))
        fmu_args['modelIdentifier'] = self.model_description.modelExchange.modelIdentifier


        if relative_tolerance is None:
            self.relative_tolerance = 1e-5
        else:
            self.relative_tolerance = relative_tolerance

        if output_interval is None:
            if step_size is None:
                self.output_interval = auto_interval(self.tau)
            else:
                self.output_interval = step_size
                while self.tau / self.output_interval > 1000:
                    self.output_interval *= 2
        if self.step_size is None:
            self.step_size = self.output_interval
           
            
            max_step = self.tau / 1000
            while self.step_size > max_step:
                self.step_size /= 2


        self.is_fmi1 = self.model_description.fmiVersion == '1.0'
        self.is_fmi2 = self.model_description.fmiVersion == '2.0'
        self.is_fmi3 = self.model_description.fmiVersion.startswith('3.0')

        callbacks = None
        if self.is_fmi1:
            self.fmu = FMU1Model(**fmu_args)
            self.fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
            self.fmu.setTime(self.time)
        elif self.is_fmi2:
            self.fmu = FMU2Model(**fmu_args)
            self.fmu.instantiate(callbacks=callbacks, loggingOn=debug_logging)
            self.fmu.setupExperiment(startTime=start_time)
        else:
            self.fmu = FMU3Model(**fmu_args)
            self.fmu.instantiate(loggingOn=debug_logging)
            self.fmu.setupExperiment(startTime=start_time)
  
        self.input = Input(self.fmu, self.model_description, self.input_signals)

        self.solver_args = {
        'nx': self.model_description.numberOfContinuousStates,
        'nz': self.model_description.numberOfEventIndicators,
        'get_x': self.fmu.getContinuousStates,
        'set_x': self.fmu.setContinuousStates,
        'get_dx': self.fmu.getContinuousStateDerivatives if self.is_fmi3 else self.fmu.getDerivatives,
        'get_z': self.fmu.getEventIndicators,
        'input': self.input
    }


    def reset(self):
        self.time = self.start 
        self.stop = self.start
        
        if self.is_fmi1:
            self.fmu.setTime(self.start)
        else:
            self.fmu.reset()

        apply_start_values(self.fmu, self.model_description, self.start_values, False)
        # initialize
        if self.is_fmi1:

            self.input.apply(self.time)

            (self.iterationConverged,
            self.stateValueReferencesChanged,
            self.stateValuesChanged,
            self.terminateSimulation,
            self.nextEventTimeDefined,
            self.nextEventTime) = self.fmu.initialize()

            if self.terminateSimulation:
                raise Exception('Model requested termination during initial event update.')

        elif self.is_fmi2:

            self.fmu.enterInitializationMode()
            self.input.apply(self.time)
            self.fmu.exitInitializationMode()

            self.newDiscreteStatesNeeded = True
            self.terminateSimulation = False

            while self.newDiscreteStatesNeeded and not self.terminateSimulation:
                # update discrete states
                (self.newDiscreteStatesNeeded,
                self.terminateSimulation,
                self.nominalsOfContinuousStatesChanged,
                self.valuesOfContinuousStatesChanged,
                self.nextEventTimeDefined, 
                self.nextEventTime) = self.fmu.newDiscreteStates()
                

            if self.terminateSimulation:
                raise Exception('Model requested termination during initial event update.')

            self.fmu.enterContinuousTimeMode()

        elif self.is_fmi3:

            self.fmu.enterInitializationMode(startTime=self.start)
            self.input.apply(self.time)
            self.fmu.exitInitializationMode()

            self.discreteStatesNeedUpdate = True
            self.terminateSimulation = False

            while self.discreteStatesNeedUpdate and not self.terminateSimulation:
                # update discrete states
                (self.discreteStatesNeedUpdate,
                self.terminateSimulation,
                self.nominalsOfContinuousStatesChanged,
                self.valuesOfContinuousStatesChanged,
                self.nextEventTimeDefined,
                self.nextEventTime) = self.fmu.updateDiscreteStates()

            self.fmu.enterContinuousTimeMode()
        # select the solver
        if self.solver_name == 'Euler':
            self.solver = ForwardEuler(**self.solver_args)
            self.fixed_step = True
        elif self.solver_name is None or self.solver_name == 'CVode':
            from fmpy.sundials import CVodeSolver
            self.solver = CVodeSolver(
                set_time=self.fmu.setTime,
                startTime=self.start,
                maxStep=self.tau / 50.,
                relativeTolerance=self.relative_tolerance,
                **self.solver_args
                    )
            self.step_size = self.output_interval
            self.fixed_step = False
        else:
            raise Exception("Unknown solver: %s. Must be one of 'Euler' or 'CVode'." % self.solver)

        # check step size
        if self.fixed_step and not np.isclose(round(self.output_interval / self.step_size) * self.step_size, self.output_interval):
            raise Exception("output_interval must be a multiple of step_size for fixed step solvers")
        
        self.do_simulation()
        self.stop = self.start + self.tau
        return self.state

    def do_simulation(self)-> None:

        recorder = Recorder(fmu=self.fmu,
                        modelDescription=self.model_description,
                        variableNames=self.output,
                        interval=self.output_interval)

        # record the values for time == start_time
        recorder.sample(self.time)
        sim_start = current_time()
        t_next = self.start
        
        # simulation loop
        while self.time < self.stop:
           

            if self.timeout is not None and (current_time() - sim_start) > self.timeout:
                break

            if self.fixed_step:
                if self.time + self.step_size < self.stop + self.eps:
                    t_next = self.time + self.step_size
                else:
                    break
            else:
                if self.time + self.eps >= t_next:  # t_next has been reached
                    # integrate to the next grid point
                    t_next = np.floor(self.time / self.output_interval) * self.output_interval + self.output_interval
                    if t_next < self.time + self.eps:
                        t_next += self.output_interval

            # get the next input event
            t_input_event = self.input.nextEvent(self.time)

            # check for input event
            input_event = t_input_event <= t_next

            if input_event:
                t_next = t_input_event

            time_event = self.nextEventTimeDefined and self.nextEventTime <= t_next

            if time_event and not self.fixed_step:
                t_next = self.nextEventTime

            if t_next - self.time > self.eps:
                # do one step
                state_event, roots_found, self.time = self.solver.step(self.time, t_next)
            else:
                # skip
                self.time = t_next

            # set the time
            self.fmu.setTime(self.time)

            # apply continuous inputs
            self.input.apply(self.time, discrete=False)

            # check for step event, e.g.dynamic state selection
            if self.is_fmi1:
                step_event = self.fmu.completedIntegratorStep()
            else:
                step_event, _ = self.fmu.completedIntegratorStep()
                step_event = step_event != fmi2False

            # handle events
            if input_event or time_event or state_event or step_event:

                if self.record_events:
                    # record the values before the event
                    recorder.sample(self.time, force=True)

                if self.is_fmi1:

                    if input_event:
                        input.apply(time=self.time, after_event=True)

                    self.iterationConverged = False

                    # update discrete states
                    while not self.iterationConverged and not self.terminateSimulation:
                        (self.iterationConverged,
                        self.stateValueReferencesChanged,
                        self.stateValuesChanged,
                        self.terminateSimulation,
                        self.nextEventTimeDefined,
                        self.nextEventTime) = self.fmu.eventUpdate()

                    if self.terminateSimulation:
                        break

                elif self.is_fmi2:

                    self.fmu.enterEventMode()

                    if input_event:
                        self.input.apply(time=self.time, after_event=True)

                    self.newDiscreteStatesNeeded = True

                    # update discrete states
                    while self.newDiscreteStatesNeeded and not self.terminateSimulation:
                        (self.newDiscreteStatesNeeded,
                        self.terminateSimulation,
                        self.nominalsOfContinuousStatesChanged,
                        self.valuesOfContinuousStatesChanged,
                        self.nextEventTimeDefined,
                        self.nextEventTime) = self.fmu.newDiscreteStates()

                    if self.terminateSimulation:
                        break

                    self.fmu.enterContinuousTimeMode()

                else:

                    self.fmu.enterEventMode(stepEvent=step_event, rootsFound=roots_found, timeEvent=time_event)

                    if input_event:
                        self.input.apply(time=self.time, after_event=True)

                    self.newDiscreteStatesNeeded = True

                    # update discrete states
                    while self.newDiscreteStatesNeeded and not self.terminateSimulation:
                        (self.newDiscreteStatesNeeded,
                        self.terminateSimulation,
                        self.nominalsOfContinuousStatesChanged,
                        self.valuesOfContinuousStatesChanged,
                        self.nextEventTimeDefined,
                        self.nextEventTime) = self.fmu.updateDiscreteStates()

                    if self.terminateSimulation:
                        break

                    self.fmu.enterContinuousTimeMode()

                self.solver.reset(self.time)

                if self.record_events:
                    # record values after the event
                    recorder.sample(self.time, force=True)

            if abs(self.time - round(self.time / self.output_interval) * self.output_interval) < self.eps and self.time > recorder.lastSampleTime + self.eps:
                # record values for this step
                recorder.sample(self.time, force=True)
        # if self.stop == self.start:
        #     print("sample time")
        #     recorder.sample(self.time, force=True)
        self.state = recorder.result()[-1]

    def close(self):

        del self.solver
        self.solver = None

        self.fmu.terminate()

        self.fmu.freeInstance()

    def _get_input(self,action):
      
        return Input(self.fmu, self.model_description, np.array(action, dtype=[(x,float) for x in self.model_input_names]))
  

 




class StatisticGameConf(MeSimulationConf):
    profiles: Dict[str,List[float]]
    start_values: Dict[str, float] = {}
    @validator('profiles')
    def check_profile_names(cls, v, values, **kwargs):
        if ('model_input_names' in values) and not set(v.keys()).issubset(set(values['model_input_names'])):
            raise ValueError('names of profiles for statistic inputs have to occure in model_input_names')
        return v
    
class MeStatisticGame(MeFMI):
    """general class for statistic games. By this we mean games coming from fmu simulations performed by model exchange
    togehter with inputs given by actions and statistic inputs. The statistics are given "beforehand" or forecasted:
    This means that the current state is given by the outputs of the last simulation of the statistics of
    the next simulation. The agent has in this sense perfect foresight.

    As an example imagine a heat buffer with a statistic load, we can not control, and an heating action, we may control
    """
    _counter = 0
    _profiles = None
   

    def __init__(self, filename, config, relative_tolerance = 1e-5# 1e-5
    ):
        
        if not isinstance(config, StatisticGameConf):
            raise TypeError("config hast to be of type StatisticGameConf")
        self._profiles = config.profiles
        
        super().__init__(filename,relative_tolerance=relative_tolerance, config=config, start_values= config.start_values)


    @property 
    def end(self):
        """last simulation step

        Returns
        -------
        int
        """
        for n in self._profiles:
            return len(self._profiles[n])

    @property
    def current_statistic(self):
        """the statistic input values of the current timestep. This means the values 
        during the *next* simulation step!

        Returns
        -------
        List[float]
        """
        return [self._profiles[n][self._counter] for n in self._profiles]

    @property
    def statistic_inputs(self):
        """the names of the statistic inputs

        Returns
        -------
        List[str]
        """
        return list(self._profiles)

    @property
    def action_inputs(self):
        """the names of the action inputs

        Returns
        -------
        List[str]
        """
        return [x for x in self.model_input_names if x not in self.statistic_inputs]

    @property
    def input_dtype(self)->List[tuple]:
        """the dtypes of all inputs

        Returns
        -------
        List[tuple]
            dtypes as needed for named/custom np.arrays
        """
        return [
    ('time', np.double)] + [
    (n, np.double) for n in self.action_inputs + self.statistic_inputs
    ]

    @property
    def output_dtype(self):
        """the dtypes of all outputs

        Returns
        -------
        list[tuple]
            dtypes as needed for named/custom np.arrays
        """
        return [
    (n, np.double) for n in self.output + self.statistic_inputs
    ]
    
    def get_current(self, name:str)->float:
        """get the current value of 1 observation

        Parameters
        ----------
        name : str
            name of varianle to be observed

        Returns
        -------
        float
            the value
        """
        x = list(self.output + self.statistic_inputs)
        return {x[i]:self.state[i] for i in range(len(x))}[name]


    def _transform_state(self, value:np.void)->np.array:
        """

        Parameters
        ----------
        value : np.array
            a named numpy void as given as ouput by the simulation by fmpy

        Returns
        -------
        np.array
        the output values of the last simulation together with the statistic input values for the next simulation
        """
        return np.array(list(value)[1:] + self.current_statistic, dtype=float)
    
    def reset(self):
        """reset the simulation game

        Returns
        -------
        np.array
            the zeroth state of the simulated system
        """
        self.failed_simulation = False
        self._counter = 0
        data = [(self.time,) + tuple(self.current_statistic)]
        data = np.array(data, dtype= [('time',float)] + [(x, float) for x in self.statistic_inputs])
        self.input = Input(self.fmu, self.model_description, data)
        super().reset()
        self._counter += 1
        return self.state
    
    def _get_input(self, action)-> Input:
        """Transform a given action to the Input of the actual simualtion:
        Add the current statistic inputs and transfrom it to fmpy.simulation.Input.

        Parameters
        ----------
        action : np.array
            the action on the game

        Returns
        -------
        Input
            fmpy.simulation.Input for fmpy simulation/ FMI
        """
        try: 
            iter(action)
        except TypeError as te:
            print("action has to be iterable")
        data = [(self.time,) + tuple(action) + tuple(self.current_statistic)]
        data = np.array(data, dtype=self.input_dtype)
        return Input(self.fmu, self.model_description, data)
    
    def step(self, action):
        """do a simulation step in the game according to the current action

        Parameters
        ----------
        action : np.array
            actionin the game

        Returns
        -------
        state : np.array
            the new state
        reward : float
            the reward gained during the step
        done : bool
            is the game over
        info : dict
            info about the simulation step
        """
        
        state, reward, done, info = super().step(action)
      
        self._counter += 1
    
        return state, reward, done, info
    
    def _is_done(self)->bool:
        """get, if the simulation is done

        Returns
        -------
        bool
            is the simualtion done
        """
        done = False
        if self._counter >= self.end - 1:
            done = True
        if self._failed_simulation:
            print("simulation failed. Terminating episode ...")
            done = True

        return done
    

