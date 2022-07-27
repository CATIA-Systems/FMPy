within FMI.Examples.FMI2.CoSimulation.FMUs;
model BouncingBall
  "This model calculates the trajectory, over time, of a ball dropped from a height of 1 m."

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

  parameter Modelica.Units.SI.Time communicationStepSize = 0.01 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Float64 'g' = -9.81 "Gravity acting on the ball";

  parameter Float64 'e' = 0.7 "Coefficient of restitution";

  Float64Output 'h' annotation (Placement(transformation(extent={ { 200, 23.33333333333333},  { 220, 43.33333333333333}}),   iconTransformation(extent={ { 200, 23.33333333333333},  { 220, 43.33333333333333}})));

  Float64Output 'v' annotation (Placement(transformation(extent={ { 200, -43.33333333333334},  { 220, -23.333333333333343}}),   iconTransformation(extent={ { 200, -43.33333333333334},  { 220, -23.333333333333343}})));

protected
  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/BouncingBall"),
    2,
    "BouncingBall",
    getInstanceName(),
    1,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f003}",
    visible,
    loggingOn,
    logFMICalls);

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

  FMI3SetFloat64(instance, {5}, 1, {'g'});
  FMI3SetFloat64(instance, {6}, 1, {'e'});

  FMI3ExitInitializationMode(instance);

equation

algorithm
  when sample(startTime, communicationStepSize) then

    FMI3DoStep(instance, time, communicationStepSize);

    'h' := FMI3GetFloat64Scalar(instance, 1, time);
    'v' := FMI3GetFloat64Scalar(instance, 3, time);

  end when;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-200,-100}, {200,100}}),
      graphics={
        Text(extent={{-200,110}, {200,150}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-200,-100},{200,100}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid),
          Text(extent={ { 10, 23.33333333333333},  { 190, 43.33333333333333}},   textColor={0,0,0}, textString="h", horizontalAlignment=TextAlignment.Right),  Text(extent={ { 10, -43.33333333333334},  { 190, -23.333333333333343}},   textColor={0,0,0}, textString="v", horizontalAlignment=TextAlignment.Right)}),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-200,-100}, {200,100}})),
    experiment(StopTime=3.0));
end BouncingBall;
