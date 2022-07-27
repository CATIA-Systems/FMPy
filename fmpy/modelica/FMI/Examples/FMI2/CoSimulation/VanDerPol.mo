within FMI.Examples.FMI2.CoSimulation;

model VanDerPol
  "This model implements the van der Pol oscillator"

  import Modelica.Blocks.Interfaces.*;
  import FMI.FMI2.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time communicationStepSize = 0.01 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Real 'mu' = 1;

  RealOutput 'x0' annotation (Placement(transformation(extent={ { 200, 23.33333333333333 }, { 220, 43.33333333333333 } }), iconTransformation(extent={ { 200, 23.33333333333333 }, { 220, 43.33333333333333 } })));

  RealOutput 'x1' annotation (Placement(transformation(extent={ { 200, -43.33333333333334 }, { 220, -23.333333333333343 } }), iconTransformation(extent={ { 200, -43.33333333333334 }, { 220, -23.333333333333343 } })));

protected

  FMI.Internal.ModelicaFunctions callbacks = FMI.Internal.ModelicaFunctions();

  FMI.Internal.ExternalFMU instance = FMI.Internal.ExternalFMU(
    callbacks,
    Modelica.Utilities.Files.loadResource("modelica://FMI/Resources/FMUs/VanDerPol"),
    1,
    "VanDerPol",
    getInstanceName(),
    1,
    "{8c4e810f-3da3-4a00-8276-176fa3c9f000}",
    visible,
    loggingOn,
    logFMICalls);

initial algorithm

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

  FMI2SetReal(instance, {5}, 1, {'mu'});

  FMI2EnterInitializationMode(instance);


  FMI2ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then


    FMI2DoStep(instance, time, communicationStepSize, true);

    'x0' := FMI2GetRealScalar(instance, 1);
    'x1' := FMI2GetRealScalar(instance, 3);

  end when;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{-200,-100}, {200,100}}),
      graphics={
        Text(extent={{-200,110}, {200,150}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{-200,-100},{200,100}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
        , Text(extent={ { 10, 23.33333333333333 }, { 190, 43.33333333333333 } }, textColor={0,0,0}, textString="x0", horizontalAlignment=TextAlignment.Right) , Text(extent={ { 10, -43.33333333333334 }, { 190, -23.333333333333343 } }, textColor={0,0,0}, textString="x1", horizontalAlignment=TextAlignment.Right)
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-200,-100}, {200,100}})),
    experiment(StopTime=20.0)
  );
end VanDerPol;