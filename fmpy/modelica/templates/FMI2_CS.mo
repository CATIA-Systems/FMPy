@@ extends "FMU.mo" @@
@@ block imports @@
  import FMI.FMI2.Interfaces.*;
  import FMI.FMI2.Functions.*;
@@ endblock @@
@@ block parameters @@

  parameter Modelica.Units.SI.Time communicationStepSize = @=communicationStepSize=@ annotation(Dialog(tab="FMI", group="Parameters"));
@@ endblock @@
@@ block equations @@

initial algorithm

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

@@ for variable in parameters @@
  FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

  FMI2EnterInitializationMode(instance);

@@ for variable in inputs @@
  FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

  FMI2ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then

@@ for variable in inputs @@
    FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

    FMI2DoStep(instance, time, communicationStepSize, true);

@@ for variable in outputs @@
    '@=variable.name=@' := FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endfor @@

  end when;
@@ endblock @@