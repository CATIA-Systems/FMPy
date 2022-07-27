within FMI.Examples.FMI3.ModelExchange;

model Feedthrough

  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Float64 'Float64_fixed_parameter' = 0;

  parameter Float64 'Float64_tunable_parameter' = 0;

  parameter Float64 'Float64_continuous_input_start' = 0;

  parameter Float64 'Float64_discrete_input_start' = 0;

  parameter Int32 'Int32_input_start' = 0;

  parameter Boolean 'Boolean_input_start' = false;

  Float64Input 'Float64_continuous_input'(start='Float64_continuous_input_start') annotation (Placement(transformation(extent={ { -640, 100.0 }, { -600, 140.0 } }), iconTransformation(extent={ { -640, 100.0 }, { -600, 140.0 } })));

  Float64Input 'Float64_discrete_input'(start='Float64_discrete_input_start') annotation (Placement(transformation(extent={ { -640, 20.0 }, { -600, 60.0 } }), iconTransformation(extent={ { -640, 20.0 }, { -600, 60.0 } })));

  Int32Input 'Int32_input'(start='Int32_input_start') annotation (Placement(transformation(extent={ { -640, -60.0 }, { -600, -20.0 } }), iconTransformation(extent={ { -640, -60.0 }, { -600, -20.0 } })));

  BooleanInput 'Boolean_input'(start='Boolean_input_start') annotation (Placement(transformation(extent={ { -640, -140.0 }, { -600, -100.0 } }), iconTransformation(extent={ { -640, -140.0 }, { -600, -100.0 } })));

  Float64Output 'Float64_continuous_output' annotation (Placement(transformation(extent={ { 600, 110.0 }, { 620, 130.0 } }), iconTransformation(extent={ { 600, 110.0 }, { 620, 130.0 } })));

  Float64Output 'Float64_discrete_output' annotation (Placement(transformation(extent={ { 600, 30.0 }, { 620, 50.0 } }), iconTransformation(extent={ { 600, 30.0 }, { 620, 50.0 } })));

  Int32Output 'Int32_output' annotation (Placement(transformation(extent={ { 600, -50.0 }, { 620, -30.0 } }), iconTransformation(extent={ { 600, -50.0 }, { 620, -30.0 } })));

  BooleanOutput 'Boolean_output' annotation (Placement(transformation(extent={ { 600, -130.0 }, { 620, -110.0 } }), iconTransformation(extent={ { 600, -130.0 }, { 620, -110.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Feedthrough"),
    2,
    "Feedthrough",
    getInstanceName(),
    0,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f004}",
    visible,
    loggingOn,
    logFMICalls);

  final constant Integer nx = 0;
  final constant Integer nz = 0;

  final constant Integer float64InputVRs[0] = fill(0, 0);
  final constant Integer int32InputVRs[0] = fill(0, 0);
  final constant Integer booleanInputVRs[1] = { 27 };

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

  FMI3SetFloat64(instance, {5}, 1, {'Float64_fixed_parameter'});
  FMI3SetFloat64(instance, {6}, 1, {'Float64_tunable_parameter'});

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

  FMI3SetFloat64(instance, {7}, 1, {'Float64_continuous_input_start'});
  FMI3SetFloat64(instance, {9}, 1, {'Float64_discrete_input_start'});
  FMI3SetInt32(instance, {19}, 1, {'Int32_input_start'});
  FMI3SetBoolean(instance, {27}, 1, {'Boolean_input_start'});

  FMI3ExitInitializationMode(instance);

  (valuesOfContinuousStatesChanged, nextEventTime) := FMI3UpdateDiscreteStates(instance);
  FMI3EnterContinuousTimeMode(instance);
  x := FMI3GetContinuousStates(instance, nx);
  instanceStartTime := time;

equation

  instanceTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, instanceTime);

  z = getEventIndicators(instance, instanceTime, fill(0.0, 0), fill(0, 0), { 'Boolean_input' });

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, fill(0, 0), { 'Boolean_input' });

  when cat(1, {time >= pre(nextEventTime)}, change(z_positive), {inputEvent}) then
    (valuesOfContinuousStatesChanged, nextEventTime) = updateDiscreteStates(instance);
  end when;

  if initial() then
    'Float64_continuous_output' = FMI3GetFloat64Scalar(instance, 8, instanceStartTime);
    'Float64_discrete_output' = FMI3GetFloat64Scalar(instance, 10, instanceStartTime);
  else
    'Float64_continuous_output' = FMI3GetFloat64Scalar(instance, 8, instanceTime);
    'Float64_discrete_output' = FMI3GetFloat64Scalar(instance, 10, instanceTime);
  end if;

algorithm
  if initial() then
    FMI3SetTime(instance, instanceStartTime);
    // FMI3SetInt32(instance, {19}, 1, {'Int32_input'});
    // FMI3SetBoolean(instance, {27}, 1, {'Boolean_input'});
    'Int32_output' := FMI3GetInt32Scalar(instance, 20, instanceStartTime);
    'Boolean_output' := FMI3GetBooleanScalar(instance, 28, instanceStartTime);
  else
    FMI3SetTime(instance, instanceTime);
    // FMI3SetInt32(instance, {19}, 1, {'Int32_input'});
    // FMI3SetBoolean(instance, {27}, 1, {'Boolean_input'});
    'Int32_output' := FMI3GetInt32Scalar(instance, 20, instanceTime);
    'Boolean_output' := FMI3GetBooleanScalar(instance, 28, instanceTime);
  end if;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-600,-200}, {600,200}}),
      graphics={
        Text(extent={{-600,210}, {600,250}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-600,-200},{600,200}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-600,-200}, {600,200}})),
    experiment(StopTime=2.0)
  );
end Feedthrough;