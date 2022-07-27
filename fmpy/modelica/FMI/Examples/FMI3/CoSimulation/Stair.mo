within FMI.Examples.FMI3.CoSimulation;

model Stair

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

  parameter Modelica.Units.SI.Time communicationStepSize = 0.2 annotation(Dialog(tab="FMI", group="Parameters"));

  Int32Output 'counter' annotation (Placement(transformation(extent={ { 200, -10.0 }, { 220, 10.0 } }), iconTransformation(extent={ { 200, -10.0 }, { 220, 10.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Stair"),
    2,
    "Stair",
    getInstanceName(),
    1,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f008}",
    visible,
    loggingOn,
    logFMICalls);

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);



  FMI3ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then


    FMI3DoStep(instance, time, communicationStepSize);

    'counter' := FMI3GetInt32Scalar(instance, 1, time);

  end when;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-200,-100}, {200,100}}),
      graphics={
        Text(extent={{-200,110}, {200,150}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-200,-100},{200,100}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
        , Text(extent={ { 10, -10.0 }, { 190, 10.0 } }, textColor={0,0,0}, textString="counter", horizontalAlignment=TextAlignment.Right)
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-200,-100}, {200,100}})),
    experiment(StopTime=10.0)
  );
end Stair;