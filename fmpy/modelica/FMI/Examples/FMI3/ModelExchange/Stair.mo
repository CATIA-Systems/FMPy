within FMI.Examples.FMI3.ModelExchange;

model Stair

  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  Int32Output 'counter' annotation (Placement(transformation(extent={ { 600, -10.0 }, { 620, 10.0 } }), iconTransformation(extent={ { 600, -10.0 }, { 620, 10.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Stair"),
    2,
    "Stair",
    getInstanceName(),
    0,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f008}",
    visible,
    loggingOn,
    logFMICalls);

  final constant Integer nx = 0;
  final constant Integer nz = 0;

  final constant Integer float64InputVRs[0] = fill(0, 0);
  final constant Integer int32InputVRs[0] = fill(0, 0);
  final constant Integer booleanInputVRs[0] = fill(0, 0);

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


  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);


  FMI3ExitInitializationMode(instance);

  (valuesOfContinuousStatesChanged, nextEventTime) := FMI3UpdateDiscreteStates(instance);
  FMI3EnterContinuousTimeMode(instance);
  x := FMI3GetContinuousStates(instance, nx);
  instanceStartTime := time;

equation

  instanceTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, instanceTime);

  z = getEventIndicators(instance, instanceTime, fill(0.0, 0), fill(0, 0), fill(false, 0));

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, fill(0, 0), fill(false, 0));

  when cat(1, {time >= pre(nextEventTime)}, change(z_positive), {inputEvent}) then
    (valuesOfContinuousStatesChanged, nextEventTime) = updateDiscreteStates(instance);
  end when;

  if initial() then
  else
  end if;

algorithm
  if initial() then
    FMI3SetTime(instance, instanceStartTime);
    'counter' := FMI3GetInt32Scalar(instance, 1, instanceStartTime);
  else
    FMI3SetTime(instance, instanceTime);
    'counter' := FMI3GetInt32Scalar(instance, 1, instanceTime);
  end if;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-600,-100}, {600,100}}),
      graphics={
        Text(extent={{-600,110}, {600,150}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-600,-100},{600,100}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-600,-100}, {600,100}})),
    experiment(StopTime=10.0)
  );
end Stair;