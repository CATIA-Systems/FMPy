@@ extends "FMU.mo" @@
@@ block imports @@
  import FMI.FMI2.Interfaces.*;
  import FMI.FMI2.Functions.*;
@@ endblock @@
@@ block equations @@

  final constant Integer nx = @=nx=@;
  final constant Integer nz = @=nz=@;

  final constant Integer realInputVRs[@=realInputVRs|length=@] = @=as_array(realInputVRs, '0')=@;
  final constant Integer integerInputVRs[@=integerInputVRs|length=@] = @=as_array(integerInputVRs, '0')=@;
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
    FMI2SetTime(instance, t);
    FMI2SetContinuousStates(instance, x, size(x, 1));
    instanceTime := t;
  end setTimeAndStates;

  impure function getDerivatives
    input FMI.Internal.ExternalFMU instance;
    input Real instanceTime;
    output Real dx[nx];
  algorithm
    dx := FMI2GetDerivatives(instance, size(dx, 1));
  end getDerivatives;

  impure function getEventIndicators
    input FMI.Internal.ExternalFMU instance;
    input Real instanceTime;
    input Real realInputs[:];
    input Integer integerInputs[:];
    input Boolean booleanInputs[:];
    output Real z[nz];
  algorithm
    FMI2SetReal(instance, realInputVRs, size(realInputs, 1), realInputs);
    // FMI2SetInteger(instance, integerInputVRs, size(integerInputs, 1), integerInputs);
    // FMI2SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    z := FMI2GetEventIndicators(instance, size(z, 1));
  end getEventIndicators;

  impure function updateDiscreteStates
    input FMI.Internal.ExternalFMU instance;
    output Boolean valuesOfContinuousStatesChanged;
    output Real nextEventTime;
  algorithm
    FMI2EnterEventMode(instance);
    (valuesOfContinuousStatesChanged, nextEventTime) := FMI2NewDiscreteStates(instance);
    FMI2EnterContinuousTimeMode(instance);
  end updateDiscreteStates;

  impure function setInputs
    input FMI.Internal.ExternalFMU instance;
    input Integer[:] integerInputs;
    input Boolean[:] booleanInputs;
    output Boolean inputEvent;
  algorithm
    FMI2SetInteger(instance, integerInputVRs, size(integerInputs, 1), integerInputs);
    FMI2SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    inputEvent :=true;
  end setInputs;

initial algorithm

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

@@ for variable in parameters @@
  FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

  FMI2EnterInitializationMode(instance);

@@ for variable in inputs @@
  FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

  FMI2ExitInitializationMode(instance);

  (valuesOfContinuousStatesChanged, nextEventTime) := FMI2NewDiscreteStates(instance);
  FMI2EnterContinuousTimeMode(instance);
  x := FMI2GetContinuousStates(instance, nx);
  instanceStartTime := time;

equation

  instanceTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, instanceTime);

  z = getEventIndicators(instance, instanceTime, @=as_quoted_array(realInputs, '0.0')=@, @=as_quoted_array(integerInputs, '0')=@, @=as_quoted_array(booleanInputs, 'false')=@);

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, @=as_quoted_array(integerInputs, '0')=@, @=as_quoted_array(booleanInputs, 'false')=@);

  when cat(1, {time >= pre(nextEventTime)}, change(z_positive), {inputEvent}) then
    (valuesOfContinuousStatesChanged, nextEventTime) = updateDiscreteStates(instance);
  end when;
@@ if nx > 0 @@

  when valuesOfContinuousStatesChanged then
    reinit(x, FMI2GetContinuousStates(instance, nx));
  end when;
@@ endif @@

  if initial() then
@@ for variable in outputs @@
@@ if variable.type == 'Real' @@
    '@=variable.name=@' = FMI2GetRealScalar(instance, @=variable.valueReference=@, instanceStartTime);
@@ endif @@
@@ endfor @@
  else
@@ for variable in outputs @@
@@ if variable.type == 'Real' @@
    '@=variable.name=@' = FMI2GetRealScalar(instance, @=variable.valueReference=@, instanceTime);
@@ endif @@
@@ endfor @@
  end if;

algorithm
  if initial() then
    FMI2SetTime(instance, instanceStartTime);
@@ for variable in inputs @@
@@ if variable.type != 'Real' @@
    // FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Real' @@
    '@=variable.name=@' := FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endif @@
@@ endfor @@
  else
    FMI2SetTime(instance, instanceTime);
@@ for variable in inputs @@
@@ if variable.type != 'Real' @@
    // FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Real' @@
    '@=variable.name=@' := FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endif @@
@@ endfor @@  end if;
@@ endblock @@