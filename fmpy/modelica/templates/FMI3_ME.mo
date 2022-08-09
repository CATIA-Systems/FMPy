@@ extends "FMU.mo" @@
@@ block imports @@
  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;
@@ endblock @@
@@ block equations @@

  final constant Integer nx = @=nx=@;
  final constant Integer nz = @=nz=@;

  final constant Integer float64InputVRs[@=float64InputVRs|length=@] = @=as_array(float64InputVRs, '0')=@;
  final constant Integer int32InputVRs[@=int32InputVRs|length=@] = @=as_array(int32InputVRs, '0')=@;
  final constant Integer booleanInputVRs[@=booleanInputVRs|length=@] = @=as_array(booleanInputVRs, '0')=@;

  parameter Real instanceStartTime(fixed=false);

  Real x[nx];
  Real z[nz];
  Real instanceTime;
  Boolean z_positive[nz];
  Boolean inputEvent;
  Boolean valuesOfContinuousStatesChanged;
  Real nextEventTime;

  impure function setTimeAndStates
    input FMI.Internal.ExternalFMU instance;
    input Real t;
    input Real x[:];
    output Real instanceTime;
  algorithm
    FMI3SetTime(instance, t);
    FMI3SetContinuousStates(instance, x, size(x, 1));
    instanceTime := t;
  end setTimeAndStates;

  impure function getDerivatives
    input FMI.Internal.ExternalFMU instance;
    input Real instanceTime;
    output Real dx[nx];
  algorithm
    dx := FMI3GetContinuousStateDerivatives(instance, size(dx, 1));
  end getDerivatives;

  impure function getEventIndicators
    input FMI.Internal.ExternalFMU instance;
    input Real instanceTime;
    input Real float64Inputs[:];
    input Integer int32Inputs[:];
    input Boolean booleanInputs[:];
    output Real z[nz];
  algorithm
    FMI3SetFloat64(instance, float64InputVRs, size(float64Inputs, 1), float64Inputs);
    // FMI3SetInt32(instance, int32InputVRs, size(int32Inputs, 1), int32Inputs);
    // FMI3SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    z := FMI3GetEventIndicators(instance, size(z, 1));
  end getEventIndicators;

  impure function updateDiscreteStates
    input FMI.Internal.ExternalFMU instance;
    output Boolean valuesOfContinuousStatesChanged;
    output Real nextEventTime;
  algorithm
    FMI3EnterEventMode(instance);
    (valuesOfContinuousStatesChanged, nextEventTime) := FMI3UpdateDiscreteStates(instance);
    FMI3EnterContinuousTimeMode(instance);
  end updateDiscreteStates;

  impure function setInputs
    input FMI.Internal.ExternalFMU instance;
    input Integer[:] int32Inputs;
    input Boolean[:] booleanInputs;
    output Boolean inputEvent;
  algorithm
    FMI3SetInt32(instance, int32InputVRs, size(int32Inputs, 1), int32Inputs);
    FMI3SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    inputEvent :=true;
  end setInputs;

initial algorithm

@@ for variable in parameters @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

@@ for variable in inputs @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

  FMI3ExitInitializationMode(instance);

  (valuesOfContinuousStatesChanged, nextEventTime) := FMI3UpdateDiscreteStates(instance);
  FMI3EnterContinuousTimeMode(instance);
  x := FMI3GetContinuousStates(instance, nx);
  instanceStartTime := time;

equation

  instanceTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, instanceTime);

  z = getEventIndicators(instance, instanceTime, @=as_quoted_array(float64Inputs, '0.0')=@, @=as_quoted_array(int32Inputs, '0')=@, @=as_quoted_array(booleanInputs, 'false')=@);

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, @=as_quoted_array(int32Inputs, '0')=@, @=as_quoted_array(booleanInputs, 'false')=@);

  when cat(1, {time >= pre(nextEventTime)}, change(z_positive), {inputEvent}) then
    (valuesOfContinuousStatesChanged, nextEventTime) = updateDiscreteStates(instance);
  end when;
@@ if nx > 0 @@

  when valuesOfContinuousStatesChanged then
    reinit(x, FMI3GetContinuousStates(instance, nx));
  end when;
@@ endif @@

  if initial() then
@@ for variable in outputs @@
@@ if variable.type == 'Float64' @@
    '@=variable.name=@' = FMI3GetFloat64Scalar(instance, @=variable.valueReference=@, instanceStartTime);
@@ endif @@
@@ endfor @@
  else
@@ for variable in outputs @@
@@ if variable.type == 'Float64' @@
    '@=variable.name=@' = FMI3GetFloat64Scalar(instance, @=variable.valueReference=@, instanceTime);
@@ endif @@
@@ endfor @@
  end if;

algorithm
  if initial() then
    FMI3SetTime(instance, instanceStartTime);
@@ for variable in inputs @@
@@ if variable.type != 'Float64' @@
    // FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Float64' @@
    '@=variable.name=@' := FMI3Get@=variable.type=@Scalar(instance, @=variable.valueReference=@, instanceStartTime);
@@ endif @@
@@ endfor @@
  else
    FMI3SetTime(instance, instanceTime);
@@ for variable in inputs @@
@@ if variable.type != 'Float64' @@
    // FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Float64' @@
    '@=variable.name=@' := FMI3Get@=variable.type=@Scalar(instance, @=variable.valueReference=@, instanceTime);
@@ endif @@
@@ endfor @@  end if;
@@ endblock @@