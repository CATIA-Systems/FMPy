@@ extends "FMU.mo" @@
@@ block parameters @@

  parameter Modelica.Units.SI.Time communicationStepSize = @=communicationStepSize=@ annotation(Dialog(tab="FMI", group="Parameters"));
@@ endblock @@
@@ block equations @@

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

@@ for variable in parameters @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

@@ for variable in inputs @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

  FMI3ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then

@@ for variable in inputs @@
    FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

    FMI3DoStep(instance, time, communicationStepSize);

@@ for variable in outputs @@
    '@=variable.name=@' := FMI3Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endfor @@

  end when;
@@ endblock @@