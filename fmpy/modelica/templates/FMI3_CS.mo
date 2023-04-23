@@ extends "FMU.mo" @@
@@ block imports @@
  import FMI.FMI3.Types.*;
  import FMI.FMI3.Interfaces.*;
  import FMI.FMI3.Functions.*;
@@ endblock @@
@@ block parameters @@

  parameter Modelica.Units.SI.Time communicationStepSize = @=communicationStepSize=@ annotation(Dialog(tab="FMI", group="Parameters"));
@@ endblock @@
@@ block equations @@
  Boolean initialized;

initial algorithm

  FMI3EnterInitializationMode(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);

@@ for variable in parameters @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

@@ for variable in inputs @@
  FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

algorithm

  when {initial(), sample(startTime, communicationStepSize)} then

@@ for variable in inputs @@
    FMI3Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

    if time >= communicationStepSize + startTime then
      if not initialized then
        FMI3ExitInitializationMode(instance);
        initialized := true;
      end if;
      FMI3DoStep(instance, time, communicationStepSize);
    end if;

@@ for variable in outputs @@
    '@=variable.name=@' := FMI3Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endfor @@

  end when;
@@ endblock @@