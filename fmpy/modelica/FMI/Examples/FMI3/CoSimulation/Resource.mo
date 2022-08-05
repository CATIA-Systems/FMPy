within FMI.Examples.FMI3.CoSimulation;

model Resource

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

  Int32Output 'y' annotation (Placement(transformation(extent={ { 600, -10.0 }, { 620, 10.0 } }), iconTransformation(extent={ { 600, -10.0 }, { 620, 10.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Resource"),
    2,
    "Resource",
    getInstanceName(),
    1,
    "{7b9c2114-2ce5-4076-a138-2cbc69e069e5}",
    visible,
    loggingOn,
    logFMICalls,
    logToFile,
    logFile);

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);



  FMI3ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then


    FMI3DoStep(instance, time, communicationStepSize);

    'y' := FMI3GetInt32Scalar(instance, 1);

  end when;

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
    experiment(StopTime=1.0)
  );
end Resource;