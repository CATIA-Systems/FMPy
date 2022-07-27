within FMI.Examples.FMI3.CoSimulation;

model Feedthrough

  import Modelica.Blocks.Interfaces.*;
  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time communicationStepSize = 1e-2 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Float64 'Float64_fixed_parameter' = 0;

  parameter Float64 'Float64_tunable_parameter' = 0;

  parameter Float64 'Float64_continuous_input_start' = 0;

  parameter Float64 'Float64_discrete_input_start' = 0;

  parameter Int32 'Int32_input_start' = 0;

  parameter Boolean 'Boolean_input_start' = false;

  Float64Input 'Float64_continuous_input'(start='Float64_continuous_input_start') annotation (Placement(transformation(extent={ { -240, 40.0 }, { -200, 80.0 } }), iconTransformation(extent={ { -240, 40.0 }, { -200, 80.0 } })));

  Float64Input 'Float64_discrete_input'(start='Float64_discrete_input_start') annotation (Placement(transformation(extent={ { -240, 0.0 }, { -200, 40.0 } }), iconTransformation(extent={ { -240, 0.0 }, { -200, 40.0 } })));

  Int32Input 'Int32_input'(start='Int32_input_start') annotation (Placement(transformation(extent={ { -240, -40.0 }, { -200, 0.0 } }), iconTransformation(extent={ { -240, -40.0 }, { -200, 0.0 } })));

  BooleanInput 'Boolean_input'(start='Boolean_input_start') annotation (Placement(transformation(extent={ { -240, -80.0 }, { -200, -40.0 } }), iconTransformation(extent={ { -240, -80.0 }, { -200, -40.0 } })));

  Float64Output 'Float64_continuous_output' annotation (Placement(transformation(extent={ { 200, 50.0 }, { 220, 70.0 } }), iconTransformation(extent={ { 200, 50.0 }, { 220, 70.0 } })));

  Float64Output 'Float64_discrete_output' annotation (Placement(transformation(extent={ { 200, 10.0 }, { 220, 30.0 } }), iconTransformation(extent={ { 200, 10.0 }, { 220, 30.0 } })));

  Int32Output 'Int32_output' annotation (Placement(transformation(extent={ { 200, -30.0 }, { 220, -10.0 } }), iconTransformation(extent={ { 200, -30.0 }, { 220, -10.0 } })));

  BooleanOutput 'Boolean_output' annotation (Placement(transformation(extent={ { 200, -70.0 }, { 220, -50.0 } }), iconTransformation(extent={ { 200, -70.0 }, { 220, -50.0 } })));

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
    logFMICalls);

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

    'Float64_continuous_output' := FMI3GetFloat64Scalar(instance, 8, time);
    'Float64_discrete_output' := FMI3GetFloat64Scalar(instance, 10, time);
    'Int32_output' := FMI3GetInt32Scalar(instance, 20, time);
    'Boolean_output' := FMI3GetBooleanScalar(instance, 28, time);

  end when;

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