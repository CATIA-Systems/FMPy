within FMI.Examples.FMI2.CoSimulation;

model Stair
  "This model generates a stair signal using time events"

  import FMI.FMI2.Interfaces.*;
  import FMI.FMI2.Functions.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logToFile = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter String logFile = getInstanceName() + ".txt" annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time communicationStepSize = 0.2 annotation(Dialog(tab="FMI", group="Parameters"));

  IntegerOutput 'counter' annotation (Placement(transformation(extent={ { 600, -10.0 }, { 620, 10.0 } }), iconTransformation(extent={ { 600, -10.0 }, { 620, 10.0 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/Stair"),
    1,
    "Stair",
    getInstanceName(),
    1,
    "{8c4e810f-3df3-4a00-8276-176fa3c9f008}",
    visible,
    loggingOn,
    logFMICalls,
    logToFile,
    logFile);

initial algorithm

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);


  FMI2EnterInitializationMode(instance);


  FMI2ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then


    FMI2DoStep(instance, time, communicationStepSize, true);

    'counter' := FMI2GetIntegerScalar(instance, 1);

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
    experiment(StopTime=10.0)
  );
end Stair;