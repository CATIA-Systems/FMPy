within FMI.Examples.FMI3.CoSimulation;

model Feedthrough

  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logToFile = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter String logFile = getInstanceName() + ".txt" annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time communicationStepSize = 1e-2 annotation(Dialog(tab="FMI", group="Parameters"));

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
    1,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f004}",
    visible,
    loggingOn,
    logFMICalls,
    logToFile,
    logFile);

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

  FMI3SetFloat64(instance, {5}, 1, {'Float64_fixed_parameter'});
  FMI3SetFloat64(instance, {6}, 1, {'Float64_tunable_parameter'});

  FMI3SetFloat64(instance, {7}, 1, {'Float64_continuous_input_start'});
  FMI3SetFloat64(instance, {9}, 1, {'Float64_discrete_input_start'});
  FMI3SetInt32(instance, {19}, 1, {'Int32_input_start'});
  FMI3SetBoolean(instance, {27}, 1, {'Boolean_input_start'});

  FMI3ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then

    FMI3SetFloat64(instance, {7}, 1, {'Float64_continuous_input'});
    FMI3SetFloat64(instance, {9}, 1, {'Float64_discrete_input'});
    FMI3SetInt32(instance, {19}, 1, {'Int32_input'});
    FMI3SetBoolean(instance, {27}, 1, {'Boolean_input'});

    FMI3DoStep(instance, time, communicationStepSize);

    'Float64_continuous_output' := FMI3GetFloat64Scalar(instance, 8);
    'Float64_discrete_output' := FMI3GetFloat64Scalar(instance, 10);
    'Int32_output' := FMI3GetInt32Scalar(instance, 20);
    'Boolean_output' := FMI3GetBooleanScalar(instance, 28);

  end when;

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