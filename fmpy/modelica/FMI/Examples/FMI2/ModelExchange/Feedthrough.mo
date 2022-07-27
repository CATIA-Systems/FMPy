within FMI.Examples.FMI2.ModelExchange;

model Feedthrough
  "A model to test different variable types, causalities and variabilities"

  import Modelica.Blocks.Interfaces.*;
  import FMI.FMI2.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real 'Float64_fixed_parameter' = 0;

  parameter Real 'Float64_tunable_parameter' = 0;

  parameter Real 'Float64_continuous_input_start' = 0;

  parameter Real 'Float64_discrete_input_start' = 0;

  parameter Integer 'Int32_input_start' = 0;

  parameter Boolean 'Boolean_input_start' = false;

  RealInput 'Float64_continuous_input'(start='Float64_continuous_input_start') annotation (Placement(transformation(extent={ { -240, 40.0 }, { -200, 80.0 } }), iconTransformation(extent={ { -240, 40.0 }, { -200, 80.0 } })));

  RealInput 'Float64_discrete_input'(start='Float64_discrete_input_start') annotation (Placement(transformation(extent={ { -240, 0.0 }, { -200, 40.0 } }), iconTransformation(extent={ { -240, 0.0 }, { -200, 40.0 } })));

  IntegerInput 'Int32_input'(start='Int32_input_start') annotation (Placement(transformation(extent={ { -240, -40.0 }, { -200, 0.0 } }), iconTransformation(extent={ { -240, -40.0 }, { -200, 0.0 } })));

  BooleanInput 'Boolean_input'(start='Boolean_input_start') annotation (Placement(transformation(extent={ { -240, -80.0 }, { -200, -40.0 } }), iconTransformation(extent={ { -240, -80.0 }, { -200, -40.0 } })));

  RealOutput 'Float64_continuous_output' annotation (Placement(transformation(extent={ { 200, 50.0 }, { 220, 70.0 } }), iconTransformation(extent={ { 200, 50.0 }, { 220, 70.0 } })));

  RealOutput 'Float64_discrete_output' annotation (Placement(transformation(extent={ { 200, 10.0 }, { 220, 30.0 } }), iconTransformation(extent={ { 200, 10.0 }, { 220, 30.0 } })));

  IntegerOutput 'Int32_output' annotation (Placement(transformation(extent={ { 200, -30.0 }, { 220, -10.0 } }), iconTransformation(extent={ { 200, -30.0 }, { 220, -10.0 } })));

  BooleanOutput 'Boolean_output' annotation (Placement(transformation(extent={ { 200, -70.0 }, { 220, -50.0 } }), iconTransformation(extent={ { 200, -70.0 }, { 220, -50.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Feedthrough"),
    1,
    "Feedthrough",
    getInstanceName(),
    0,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f004}",
    visible,
    loggingOn,
    logFMICalls);

  final constant Integer nx = 0;
  final constant Integer nz = 0;

  final constant Integer realInputVRs[2] = { 7, 9 };
  final constant Integer integerInputVRs[1] = { 19 };
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

  FMI2SetReal(instance, {5}, 1, {'Float64_fixed_parameter'});
  FMI2SetReal(instance, {6}, 1, {'Float64_tunable_parameter'});

  FMI2EnterInitializationMode(instance);

  FMI2SetReal(instance, {7}, 1, {'Float64_continuous_input_start'});
  FMI2SetReal(instance, {9}, 1, {'Float64_discrete_input_start'});
  FMI2SetInteger(instance, {19}, 1, {'Int32_input_start'});
  FMI2SetBoolean(instance, {27}, 1, {'Boolean_input_start'});

  FMI2ExitInitializationMode(instance);

  (valuesOfContinuousStatesChanged, nextEventTime) := FMI2NewDiscreteStates(instance);
  FMI2EnterContinuousTimeMode(instance);
  x := FMI2GetContinuousStates(instance, nx);
  instanceStartTime := time;

equation

  instanceTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, instanceTime);

  z = getEventIndicators(instance, instanceTime, { 'Float64_continuous_input', 'Float64_discrete_input' }, { 'Int32_input' }, { 'Boolean_input' });

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, { 'Int32_input' }, { 'Boolean_input' });

  when cat(1, {time >= pre(nextEventTime)}, change(z_positive), {inputEvent}) then
    (valuesOfContinuousStatesChanged, nextEventTime) = updateDiscreteStates(instance);
  end when;

  if initial() then
    'Float64_continuous_output' = FMI2GetRealScalar(instance, 8, instanceStartTime);
    'Float64_discrete_output' = FMI2GetRealScalar(instance, 10, instanceStartTime);
  else
    'Float64_continuous_output' = FMI2GetRealScalar(instance, 8, instanceTime);
    'Float64_discrete_output' = FMI2GetRealScalar(instance, 10, instanceTime);
  end if;

algorithm
  if initial() then
    FMI2SetTime(instance, instanceStartTime);
    // FMI2SetInteger(instance, {19}, 1, {'Int32_input'});
    // FMI2SetBoolean(instance, {27}, 1, {'Boolean_input'});
    'Int32_output' := FMI2GetIntegerScalar(instance, 20);
    'Boolean_output' := FMI2GetBooleanScalar(instance, 28);
  else
    FMI2SetTime(instance, instanceTime);
    // FMI2SetInteger(instance, {19}, 1, {'Int32_input'});
    // FMI2SetBoolean(instance, {27}, 1, {'Boolean_input'});
    'Int32_output' := FMI2GetIntegerScalar(instance, 20);
    'Boolean_output' := FMI2GetBooleanScalar(instance, 28);
  end if;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-200,-100}, {200,100}}),
      graphics={
        Text(extent={{-200,110}, {200,150}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-200,-100},{200,100}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
        , Text(extent={ { -190, 50.0 }, { -10, 70.0 } }, textColor={0,0,0}, textString="Float64_continuous_input", horizontalAlignment=TextAlignment.Left) , Text(extent={ { -190, 10.0 }, { -10, 30.0 } }, textColor={0,0,0}, textString="Float64_discrete_input", horizontalAlignment=TextAlignment.Left) , Text(extent={ { -190, -30.0 }, { -10, -10.0 } }, textColor={0,0,0}, textString="Int32_input", horizontalAlignment=TextAlignment.Left) , Text(extent={ { -190, -70.0 }, { -10, -50.0 } }, textColor={0,0,0}, textString="Boolean_input", horizontalAlignment=TextAlignment.Left) , Text(extent={ { 10, 50.0 }, { 190, 70.0 } }, textColor={0,0,0}, textString="Float64_continuous_output", horizontalAlignment=TextAlignment.Right) , Text(extent={ { 10, 10.0 }, { 190, 30.0 } }, textColor={0,0,0}, textString="Float64_discrete_output", horizontalAlignment=TextAlignment.Right) , Text(extent={ { 10, -30.0 }, { 190, -10.0 } }, textColor={0,0,0}, textString="Int32_output", horizontalAlignment=TextAlignment.Right) , Text(extent={ { 10, -70.0 }, { 190, -50.0 } }, textColor={0,0,0}, textString="Boolean_output", horizontalAlignment=TextAlignment.Right)
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-200,-100}, {200,100}})),
    experiment(StopTime=2.0)
  );
end Feedthrough;